#!/usr/bin/env python
# Copyright (C) 2008-2009 AG Projects. See LICENSE for details.
#

import fcntl
import os
import re
import struct
import sys
import termios

from collections import deque
from optparse import OptionParser

from sipsimple.account import Account, BonjourAccount, AccountManager
from sipsimple.configuration import Setting, SettingsGroupMeta, ConfigurationManager, DefaultValue
from sipsimple.configuration.backend.configfile import ConfigFileBackend
from sipsimple.configuration.settings import SIPSimpleSettings


def format_child(obj, attrname, maxchars):
    linebuf = attrname
    if isinstance(getattr(type(obj), attrname, None), Setting):
        string = str(getattr(obj, attrname))
        if maxchars is not None:
            maxchars -= len(attrname)+4
            if len(string) > maxchars:
                string = '(..)'+string[-(maxchars-4):]
        linebuf += ' = ' + string
    return linebuf

def display_object(obj, name):
    # get terminal width
    if sys.stdout.isatty():
        width = struct.unpack('HHHH', fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, struct.pack('HHHH', 0, 0, 0, 0)))[1]
    else:
        width = None

    children = deque([child for child in dir(type(obj)) if isinstance(getattr(type(obj), child, None), Setting)] + \
                     [child for child in dir(type(obj)) if isinstance(getattr(type(obj), child, None), SettingsGroupMeta)])
    # display first line
    linebuf = ' '*(len(name)+3) + '+'
    if children:
        linebuf += '-- ' + format_child(obj, children.popleft(), width-(len(name)+7) if width is not None else None)
    print linebuf
    # display second line
    linebuf = name + ' --|'
    if children:
        linebuf += '-- ' + format_child(obj, children.popleft(), width-(len(name)+7) if width is not None else None)
    print linebuf
    # display the rest of the lines
    if children:
        while children:
            child = children.popleft()
            linebuf = ' '*(len(name)+3) + ('|' if children else '+') + '-- ' + format_child(obj, child, width-(len(name)+7) if width is not None else None)
            print linebuf
    else:
        linebuf = ' '*(len(name)+3) + '+'
        print linebuf

    print
    
    [display_object(getattr(obj, child), child) for child in dir(type(obj)) if isinstance(getattr(type(obj), child, None), SettingsGroupMeta)]

class SettingsParser(object):

    @classmethod
    def parse_default(cls, type, value):
        if issubclass(type, (tuple, list)):
            values = re.split(r'\s*,\s*', value)
            return values
        elif issubclass(type, bool):
            if value.lower() == 'true':
                return True
            else:
                return False
        else:
            return value
    
    @classmethod
    def parse_LocalIPAddress(cls, type, value):
        if value == 'auto':
            return type()
        return type(value)

    @classmethod
    def parse_MSRPRelayAddress(cls, type, value):
        match = re.match(r'^(?P<host>(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})|([a-zA-Z0-9\-_]+(\.[a-zA-Z0-9\-_]+)*))(:(?P<port>\d+))?(;transport=(?P<transport>[a-z]+))?$', value)
        if match is None:
            raise ValueError("illegal value for address: %s" % value)
        match_dict = match.groupdict()
        if match_dict['port'] is None:
            del match_dict['port']
        if match_dict['transport'] is None:
            del match_dict['transport']
        return type(**match_dict)

    parse_SIPProxy = parse_MSRPRelayAddress

    @classmethod
    def parse_PortRange(cls, type, value):
        return type(*value.split(':', 1))

    @classmethod
    def parse_Resolution(cls, type, value):
        return type(*value.split('x', 1))

    @classmethod
    def parse_SoundFile(cls, type, value):
        if ',' in value:
            path, volume = value.split(',', 1)
        else:
            path, volume = value, 100
        return type(path, volume)

    @classmethod
    def parse(cls, type, value):
        if value == 'None':
            return None
        if value == 'DEFAULT':
            return DefaultValue
        parser = getattr(cls, 'parse_%s' % type.__name__, cls.parse_default)
        return parser(type, value)


class AccountConfigurator(object):
    def __init__(self, config_file):
        self.configuration_manager = ConfigurationManager()
        if config_file is not None:
            self.configuration_manager.start(ConfigFileBackend(os.path.realpath(config_file)))
        else:
            self.configuration_manager.start()
        self.account_manager = AccountManager()
        self.account_manager.start()

    def list(self):
        print 'Accounts:'
        bonjour_account = BonjourAccount()
        accounts = [account for account in self.account_manager.get_accounts() if account.id != bonjour_account.id]
        accounts.sort(cmp=lambda a, b: cmp(a.id, b.id))
        accounts.append(bonjour_account)
        for account in accounts:
            print '  %s (%s)%s' % (account.id, 'enabled' if account.enabled else 'disabled', ' - default_account' if account is self.account_manager.default_account else '')

    def add(self, sip_address, password):
        if self.account_manager.has_account(sip_address):
            print 'Account %s already exists' % sip_address
            return
        try:
            account = Account(sip_address)
        except ValueError, e:
            print 'Cannot add SIP account: %s' % str(e)
            return
        account.password = password
        account.enabled = True
        account.save()
        print 'Account added'

    def delete(self, sip_address):
        if sip_address != 'ALL':
            possible_accounts = [account for account in self.account_manager.iter_accounts() if sip_address in account.id]
            if len(possible_accounts) > 1:
                print "More than one account exists which matches %s: %s" % (sip_address, ", ".join(sorted(account.id for account in possible_accounts)))
                return
            if len(possible_accounts) == 0:
                print 'Account %s does not exist' % sip_address
                return
            account = possible_accounts[0]
            if account == BonjourAccount():
                print 'Cannot delete bonjour account'
                return
            account.delete()
            print 'Account deleted'
        else:
            for account in self.account_manager.get_accounts():
                account.delete()
            print 'Accounts deleted'

    def show(self, sip_address=None):
        if sip_address is None:
            accounts = [self.account_manager.default_account]
            if accounts[0] is None:
                print "No accounts configured"
                return
        else:
            if sip_address != 'ALL':
                accounts = [account for account in self.account_manager.iter_accounts() if sip_address in account.id]
            else:
                accounts = self.account_manager.get_accounts()
            if not accounts:
                print 'No accounts which match %s' % sip_address
                return
        for account in accounts:
            print 'Account %s:' % account.id
            display_object(account, 'account')

    def set(self, *args):
        if not args:
            raise TypeError("set must receive at least one argument")
        if '=' in args[0]:
            accounts = [self.account_manager.default_account]
            if accounts[0] is None:
                print "No accounts configured"
                return
        else:
            sip_address = args[0]
            args = args[1:]
            if sip_address != 'ALL':
                accounts = [account for account in self.account_manager.iter_accounts() if sip_address in account.id]
            else:
                accounts = self.account_manager.get_accounts()
            if not accounts:
                print 'No accounts which match %s' % sip_address
                return
        
        try:
            settings = dict(arg.split('=', 1) for arg in args)
        except ValueError:
            print 'Illegal arguments: %s' % ' '.join(args)
            return
        
        for account in accounts:
            for attrname, value in settings.iteritems():
                object = account
                name = attrname
                while '.' in name:
                    local_name, name = name.split('.', 1)
                    try:
                        object = getattr(object, local_name)
                    except AttributeError:
                        print 'Unknown setting: %s' % attrname
                        object = None
                        break
                if object is not None:
                    try:
                        attribute = getattr(type(object), name)
                        value = SettingsParser.parse(attribute.type, value)
                        setattr(object, name, value)
                    except AttributeError:
                        print 'Unknown setting: %s' % attrname
                    except ValueError, e:
                        print '%s: %s' % (attrname, str(e))
            
            account.save()
        print 'Account%s updated' % ('s' if len(accounts) > 1 else '')

    def default(self, sip_address):
        possible_accounts = [account for account in self.account_manager.iter_accounts() if sip_address in account.id]
        if len(possible_accounts) > 1:
            print "More than one account exists which matches %s: %s" % (sip_address, ", ".join(sorted(account.id for account in possible_accounts)))
            return
        if len(possible_accounts) == 0:
            print 'Account %s does not exist' % sip_address
            return
        account = possible_accounts[0]
        try:
            self.account_manager.default_account = account
        except ValueError, e:
            print str(e)
            return
        print 'Account %s is now default account' % account.id


class SIPSimpleConfigurator(object):
    def __init__(self, config_file):
        self.configuration_manager = ConfigurationManager()
        if config_file is not None:
            self.configuration_manager.start(ConfigFileBackend(os.path.realpath(config_file)))
        else:
            self.configuration_manager.start()

    def show(self):
        print 'SIP SIMPLE settings:'
        display_object(SIPSimpleSettings(), 'SIP SIMPLE')

    def set(self, *args):
        sipsimple_settings = SIPSimpleSettings()
        try:
            settings = dict(arg.split('=', 1) for arg in args)
        except ValueError:
            print 'Illegal arguments: %s' % ' '.join(args)
            return
        
        for attrname, value in settings.iteritems():
            object = sipsimple_settings
            name = attrname
            while '.' in name:
                local_name, name = name.split('.', 1)
                try:
                    object = getattr(object, local_name)
                except AttributeError:
                    print 'Unknown setting: %s' % attrname
                    object = None
                    break
            if object is not None:
                try:
                    attribute = getattr(type(object), name)
                    value = SettingsParser.parse(attribute.type, value)
                    setattr(object, name, value)
                except AttributeError:
                    print 'Unknown setting: %s' % attrname
                except ValueError, e:
                    print '%s: %s' % (attrname, str(e))
        
        sipsimple_settings.save()
        print 'SIP SIMPLE general settings updated'


if __name__ == '__main__':
    description = "This script is used to manage the SIP SIMPLE middleware settings."
    usage = """%prog [--general|--account] command [arguments]
       %prog --general show
       %prog --general set key1=value1 [key2=value2 ...]
       %prog --account list
       %prog --account add user@domain password
       %prog --account delete user@domain|ALL
       %prog --account show [user@domain|ALL]
       %prog --account set [user@domain|ALL] key1=value1 [key2=value2 ...]
       %prog --account default user@domain"""
    parser = OptionParser(usage=usage, description=description)
    parser.add_option('-c', '--config-file', type='string', dest='config_file', help='The path to a configuration file to use. This overrides the default location of the configuration file.', metavar='FILE')
    parser.add_option("-a", "--account", action="store_true", dest="account", help="Manage SIP accounts' settings")
    parser.add_option("-g", "--general", action="store_true", dest="general", help="Manage general SIP SIMPLE middleware settings")
    options, args = parser.parse_args()
    # exactly one of -a or -g must be specified
    if (not (options.account or options.general)) or (options.account and options.general):
        parser.print_usage()
        sys.exit(1)

    # there must be at least one command
    if not args:
        sys.stderr.write("Error: no command specified\n")
        parser.print_usage()
        sys.exit(1)

    # execute the handlers
    if options.account:
        object = AccountConfigurator(options.config_file)
    else:
        object = SIPSimpleConfigurator(options.config_file)
    command, args = args[0], args[1:]
    handler = getattr(object, command, None)
    if handler is None or not callable(handler):
        sys.stderr.write("Error: illegal command: %s\n" % command)
        parser.print_usage()
        sys.exit(1)
    
    try:
        handler(*args)
    except TypeError:
        sys.stderr.write("Error: illegal usage of command %s\n" % command)
        parser.print_usage()
        sys.exit(1)


