---
name: mobile-ads-orchestration
description: Designs, implements, reviews, and debugs mobile advertising flows across Flutter and Android native, including banner, interstitial, rewarded, app-open, and native ads. Use when changing ad loading, preload/cache behavior, ad display, reward callbacks, premium ad removal, lifecycle handling, loading UI, or Flutter-to-native ad bridges.
---

# Mobile Ads Orchestration

Treat each ad as an explicit state machine. Never let an SDK callback directly control unrelated UI, rewards, navigation, or premium state.

## Ad State Model

Use explicit states such as:

```text
idle → loading → ready → showing → consumed
              ↘ failed
```

Track placement, format, request ID, retry count, lifecycle owner, and whether the ad is eligible to show. Ignore callbacks from superseded requests.

## Mandatory Loading Overlay

For every ad format except native ads, show one app-level loading overlay while that ad is loading for display:

- banner;
- interstitial;
- rewarded;
- app-open;
- any future full-screen format.

The overlay must:

- cover the current app surface and block duplicate taps;
- have one shared owner so multiple ad requests cannot stack overlays;
- identify the active placement/request and ignore stale completion callbacks;
- remain visible until the ad becomes ready and is shown, or until load fails, times out, or is cancelled;
- dismiss before returning control to the app after failure or cancellation;
- not grant rewards or navigate by itself.

Do not show this full-screen overlay for native ads. Native ads render inside their assigned UI placement; use a local placeholder, skeleton, or reserved slot while they load so the surrounding layout remains stable.

## Loading And Show Flow

1. Validate premium state, consent, network policy, placement eligibility, and lifecycle owner.
2. Create a request ID and enter `loading`.
3. Show the global loading overlay for non-native formats; show a local placeholder for native ads.
4. On load success, enter `ready`.
5. For a full-screen placement, dismiss the overlay only when handing off to the SDK show call. For banners, dismiss it once the banner is attached to its target container.
6. On failure, timeout, cancellation, or invalid lifecycle, clear the request, dismiss the overlay/local placeholder, and use the defined fallback.
7. Destroy or release consumed ads and preload the next eligible request only after lifecycle checks.

## Format Rules

- Interstitial: do not navigate until show/dismiss callback policy is explicit.
- Rewarded: grant the reward once, only from a valid reward callback; handle dismissal without reward.
- App-open: never show over consent, payment, permission, or another full-screen ad.
- Banner: attach one live banner per placement; prevent duplicate views and refresh loops.
- Native: keep SDK view lifecycle scoped to its placement; never use the global ad-loading overlay.

## Premium And Consent

- Premium/ad-free state must cancel queued loads, hide overlays, and prevent future show calls.
- Consent/age/privacy gates must complete before requesting ads.
- Keep test ad unit IDs separate from production configuration.

## Flutter And Native Bridge

When Flutter delegates ads to Android native, document and index:

```text
Flutter placement request
→ MethodChannel invocation
→ Android ad manager request ID
→ SDK callback
→ MethodChannel result/event
→ Flutter overlay/state update
```

Return typed outcomes such as `shown`, `dismissed`, `rewarded`, `failed`, `not_ready`, and `skipped_premium`; do not encode control flow in message strings.

## Verification Matrix

Verify each affected format for:

- first load, cached load, failed/no-fill load, and timeout;
- duplicate tap while loading;
- app background/resume, rotation, and destroyed Activity;
- premium transition while loading;
- navigation during load and after dismissal;
- rewarded completion and dismissal without reward;
- native placement loading without the global overlay.

Use `runtime-ui-inspection` to capture the overlay and the native placeholder state. Record race conditions, callback order, and regression evidence in bug-memory shards.
