include ../../../build.mak
include ../../../build/common.mak
include ../os-$(OS_NAME).mak

export LIBDIR := ../../lib

RULES_MAK := $(PJDIR)/build/rules.mak

export ZSRTP_LIB := libzsrtp-$(TARGET_NAME)$(LIBEXT)

ifeq ($(PJ_SHARED_LIBRARIES),)
else
export ZSRTP_SONAME := libzsrtp.$(SHLIB_SUFFIX)
export ZSRTP_SHLIB := $(ZSRTP_SONAME).$(PJ_VERSION_MAJOR)
endif

###############################################################################
# Gather all flags.
#
export _CFLAGS 	:= $(CC_INC). $(CC_INC)../../zsrtp/include \
		   $(CC_INC)../../zsrtp/zrtp \
		   $(CC_INC)../../zsrtp/zrtp/zrtp \
		   $(CC_INC)../../zsrtp/zrtp/zrtp/libzrtpcpp \
		   $(CC_INC)../../zsrtp/zrtp/srtp \
		   $(CC_INC)../../zsrtp/zrtp/srtp/crypto \
		   $(CC_INC)../../../pjlib/include \
		   $(CC_INC)../../../pjlib-util/include \
		   $(CC_INC)../../../pjmedia/include \
		   $(CC_CFLAGS) $(OS_CFLAGS) $(HOST_CFLAGS) $(M_CFLAGS) \
		   $(CFLAGS)  -fno-strict-aliasing
export _CXXFLAGS:= $(_CFLAGS) $(CC_CXXFLAGS) $(OS_CXXFLAGS) $(M_CXXFLAGS) \
		   $(HOST_CXXFLAGS) $(CXXFLAGS) -std=c++11
export _LDFLAGS := $(CC_LDFLAGS) $(OS_LDFLAGS) $(M_LDFLAGS) $(HOST_LDFLAGS) \
		   $(LDFLAGS) -lsqlite3 -lstdc++

ciphersossl = zrtp/srtp/crypto/openssl/SrtpSymCrypto.o \
    	      zrtp/srtp/crypto/openssl/hmac.o \
	      zrtp/zrtp/crypto/openssl/zrtpDH.o \
	      zrtp/zrtp/crypto/openssl/hmac256.o \
	      zrtp/zrtp/crypto/openssl/sha256.o \
	      zrtp/zrtp/crypto/openssl/hmac384.o \
	      zrtp/zrtp/crypto/openssl/sha384.o \
	      zrtp/zrtp/crypto/openssl/aesCFB.o

skeinmac = zrtp/cryptcommon/skein.o \
	   zrtp/cryptcommon/skein_block.o \
	   zrtp/cryptcommon/skeinApi.o \
    	   zrtp/cryptcommon/macSkein.o \
	   zrtp/zrtp/crypto/skein256.o \
	   zrtp/zrtp/crypto/skein384.o \
	   zrtp/zrtp/crypto/skeinMac256.o \
	   zrtp/zrtp/crypto/skeinMac384.o

twofish = zrtp/cryptcommon/twofish.o \
	  zrtp/cryptcommon/twofish_cfb.o \
	  zrtp/zrtp/crypto/twoCFB.o

common = zrtp/common/osSpecifics.o

# Gcrypt support currently not tested
#ciphersgcrypt = crypto/gcrypt/gcryptAesSrtp.o crypto/gcrypt/gcrypthmac.o \
#          crypto/gcrypt/InitializeGcrypt.o

zrtpobj = zrtp/zrtp/ZrtpCallbackWrapper.o \
          zrtp/zrtp/ZIDCacheDb.o \
          zrtp/zrtp/ZIDRecordDb.o \
          zrtp/zrtp/zrtpCacheSqliteBackend.o \
          zrtp/zrtp/ZRtp.o \
          zrtp/zrtp/ZrtpCrc32.o \
          zrtp/zrtp/ZrtpPacketCommit.o \
          zrtp/zrtp/ZrtpPacketConf2Ack.o \
          zrtp/zrtp/ZrtpPacketConfirm.o \
          zrtp/zrtp/ZrtpPacketDHPart.o \
          zrtp/zrtp/ZrtpPacketGoClear.o \
          zrtp/zrtp/ZrtpPacketClearAck.o \
          zrtp/zrtp/ZrtpPacketHelloAck.o \
          zrtp/zrtp/ZrtpPacketHello.o \
          zrtp/zrtp/ZrtpPacketError.o \
          zrtp/zrtp/ZrtpPacketErrorAck.o \
          zrtp/zrtp/ZrtpPacketPingAck.o \
          zrtp/zrtp/ZrtpPacketPing.o \
          zrtp/zrtp/ZrtpPacketSASrelay.o \
          zrtp/zrtp/ZrtpPacketRelayAck.o \
          zrtp/zrtp/ZrtpStateClass.o \
          zrtp/zrtp/ZrtpTextData.o \
          zrtp/zrtp/ZrtpConfigure.o \
          zrtp/zrtp/ZrtpCWrapper.o \
          zrtp/zrtp/EmojiBase32.o \
          zrtp/zrtp/Base32.o \
          zrtp/zrtp/zrtpB64Encode.o \
          zrtp/zrtp/zrtpB64Decode.o

srtpobj = srtp/ZsrtpCWrapper.o \
	  zrtp/srtp/CryptoContext.o \
	  zrtp/srtp/CryptoContextCtrl.o

cryptobj =  $(ciphersossl) $(skeinmac) $(twofish)

export ZSRTP_SRCDIR = ../../zsrtp
export ZSRTP_OBJS = $(zrtpobj) $(cryptobj) $(srtpobj) $(common)
export ZSRTP_CFLAGS = $(_CFLAGS)
export ZSRTP_CXXFLAGS = $(_CXXFLAGS)
export ZSRTP_LDFLAGS = $(PJLIB_LDLIB) $(_LDFLAGS)


export CC_OUT CC AR RANLIB HOST_MV HOST_RM HOST_RMDIR HOST_MKDIR OBJEXT LD LDOUT
###############################################################################
# Main entry
#
# $(TARGET) is defined in os-$(OS_NAME).mak file in current directory.
#
TARGETS := $(ZSRTP_LIB) $(ZSRTP_SONAME)

all: $(TARGETS)

doc:
	cd .. && doxygen docs/doxygen.cfg

dep: depend
distclean: realclean

.PHONY: dep depend libzsrtp clean realclean distclean

.PHONY: $(TARGETS)
.PHONY: $(ZSRTP_LIB) $(ZSRTP_SONAME)

libzsrtp: $(ZSRTP_LIB)
$(ZSRTP_SONAME): $(ZSRTP_LIB)
$(ZSRTP_LIB) $(ZSRTP_SONAME):
	$(MAKE) -f $(RULES_MAK) APP=ZSRTP app=libzsrtp $(subst /,$(HOST_PSEP),$(LIBDIR)/$@)

#$(MAKE) -f $(RULES_MAK) APP=ZSRTP app=libzsrtp $(ZSRTP_LIB)


clean print_lib:
	$(MAKE) -f $(RULES_MAK) APP=ZSRTP app=libzsrtp $@

realclean:
	$(subst @@,$(subst /,$(HOST_PSEP),.ilbc-$(TARGET_NAME).depend),$(HOST_RMR))
	$(MAKE) -f $(RULES_MAK) APP=ZSRTP app=libzsrtp $@

depend:
	$(MAKE) -f $(RULES_MAK) APP=ZSRTP app=libzsrtp $@

