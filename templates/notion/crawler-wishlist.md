# Crawler Wishlist

Running notes during manual audits. Anything you check by hand that the future BL-14 crawler should also check goes here. By customer 10 this becomes the spec for the crawler.

Use this format:

```
## Audit YYYY-MM-DD — {app name}

- Checked manually: ___
- Crawler could catch this if: ___
- Pattern observed: ___
- False positive risk: ___
```

---

## Audit YYYY-MM-DD — Example

- Checked manually: whether the "Get Started" button on the homepage actually creates an account or just opens a modal that does nothing
- Crawler could catch this if: it clicks the primary CTA in a fresh context, waits 3s, and checks whether the URL changed OR a modal appeared
- Pattern observed: 3 of 5 audited Lovable apps had a CTA that opened an empty modal
- False positive risk: legitimate "Schedule a demo" modals that should not be flagged
