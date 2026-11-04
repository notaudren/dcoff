TARGET := iphone:clang:latest:15.0
ARCHS = arm64 arm64e
THEOS_PACKAGE_SCHEME = rootless

include $(THEOS)/makefiles/common.mk

TWEAK_NAME = dcoff
dcoff_FILES = Tweak.x
dcoff_CFLAGS = -fobjc-arc
dcoff_FRAMEWORKS = Foundation

include $(THEOS_MAKE_PATH)/tweak.mk
