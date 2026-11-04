// dcoff — neuter Apple DeviceCheck at the DAEMON level (devicecheckd), OUT of Snapchat's process.
// Rationale: any dylib injected INTO Snapchat is detectable (LC_ID_DYLIB / infoArray / memory scan;
// beats Shadow) -> SS03. So we do NOTHING inside Snap. DeviceCheck tokens are minted by the system
// daemon devicecheckd (via XPC); we intercept the token request THERE and return an error. Snapchat's
// -[DCDevice generateTokenWithCompletionHandler:] then receives (nil, error) over XPC -> treats
// DeviceCheck as unavailable -> falls back to App Attest relay. Snapchat's address space stays 100%
// clean (no injection), so it passes jailbreak detection, while the banned DeviceCheck token is never
// produced (no SS06). App Attest (DCAppAttestService / appAttestation*) is a SEPARATE path -> untouched.
//
// Hook target confirmed live (devicecheckd, iOS 16.7.x):
//   -[DCClientHandler fetchOpaqueBlobWithCompletion:]  = the XPC entry point for a token request.
// Filtered to the devicecheckd executable only (Executables filter in the plist).
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
