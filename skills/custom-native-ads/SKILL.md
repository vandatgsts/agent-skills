---
name: custom-native-ads
description: Designs, implements, reviews, and debugs custom-rendered native ads using an existing mobile ads library in Flutter or Android. Use when creating a native ad placement, binding native ad assets to a custom UI, managing native ad lifecycle, placeholders, reuse, premium removal, or platform-view bridges.
---

# Custom Native Ads

Use the existing ads library as the source of ad data, view registration, click handling, and lifecycle. Customize the placement UI without recreating or bypassing SDK-required behavior.

## Before Implementation

1. Identify the existing native-ad loader, ad model/view type, placement ID, premium gate, and dispose/destroy API.
2. Read the library documentation or existing implementation before designing the custom layout.
3. Define placement states: loading, loaded, unavailable, failed, and premium-hidden.
4. Keep the placement independent from full-screen ad loading overlays.

## Placement States

```text
loading     → local skeleton/reserved slot
loaded      → registered custom native ad view
unavailable → hidden slot or defined fallback
failed      → hidden slot or retry policy
premium     → no request and no slot
```

Never show the app-level loading overlay for native ads. Reserve layout space or show a local skeleton to avoid content jumping.

## Asset Binding Rules

Bind only assets supplied by the loaded ad and handle each as optional:

- headline;
- body;
- call to action;
- advertiser;
- icon;
- media content;
- price, store, and star rating when supported;
- AdChoices / attribution and SDK-required views.

- Do not invent claims, ratings, logos, or CTA text.
- Do not hide or obscure required ad attribution, media, or disclosure elements.
- Keep the CTA visually distinct but let the SDK own click registration.
- Do not place deceptive UI controls over ad assets or programmatically trigger clicks.

## Android And Flutter Integration

- Android Compose: use the library-supported native view/container bridge; create and destroy the SDK view with the composable lifecycle.
- Flutter: use the existing platform-view/widget bridge; keep the native ad object on the platform side when required by the library.
- Pass placement ID and a typed display state across any bridge. Do not serialize SDK ad objects through MethodChannel.
- Keep ad request/load logic outside the leaf UI component.

## Lifecycle And Caching

- Keep one active ad/view per placement unless the library explicitly supports pooling.
- Destroy/unregister the native ad when its owner is disposed, replaced, premium-hidden, or no longer valid.
- Ignore load callbacks for stale placement request IDs.
- Do not reuse an expired ad or attach one native view to multiple containers.
- Cancel/hide native placements immediately after premium/ad-free state changes.

## Verification

Verify with test ads and the existing library's test mode:

- loading skeleton does not use the global overlay;
- every optional asset can be absent without a broken layout;
- portrait/landscape, dark/light theme, font scale, and narrow widths;
- scroll/recomposition/navigation does not duplicate or leak views;
- premium state hides the placement and prevents reload;
- click/CTA/AdChoices behavior remains SDK-compliant.

Use `runtime-ui-inspection` for visual review and record any lifecycle or rendering regressions in bug-memory shards.
