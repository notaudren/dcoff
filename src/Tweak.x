#import <Foundation/Foundation.h>
#import <os/log.h>

@interface DCClientHandler : NSObject
@end

%hook DCClientHandler
- (void)fetchOpaqueBlobWithCompletion:(void (^)(NSData *blob, NSError *error))completion {
    os_log(OS_LOG_DEFAULT, "[dcoff] DeviceCheck fetchOpaqueBlob intercepted in devicecheckd -> error");
    if (completion) {
        completion(nil, [NSError errorWithDomain:@"com.apple.devicecheck.error" code:1 userInfo:nil]);
        return;
    }
    %orig;
}
%end

%ctor {
    os_log(OS_LOG_DEFAULT, "[dcoff] loaded into %{public}@", [[NSProcessInfo processInfo] processName]);
}
