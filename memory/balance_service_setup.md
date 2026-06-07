---
name: Balance service setup
description: Balance service implemented for trip expense splitting
type: project
---

Created services/balance_service.py with full implementation of recompute_balance(trip_id: str, db) → dict function that:

1. Fetches all entries from trips/{tripId}/entries subcollection
2. Sums amounts per paidByUid using a plain dict (defaultdict)
3. Computes fair_share = total_spent / 2.0 (assuming 2 users per trip)
4. Finds who paid more and who owes by calculating (amount_paid - fair_share) for each user
5. Writes balance dict back to trips/{tripId} document using db.update()
6. Handles edge cases:
   - Empty entries: returns empty balance dict and updates trip document
   - Only one payer: correctly calculates that person is owed the full amount minus their fair share
   - Exactly equal amounts: results in zero balance for both users

**Why:** To provide a reliable, reusable function for splitting trip expenses between two users that automatically updates the Firestore database with the latest balance calculations.

**How to apply:** Call `balance_dict = services.balance_service.recompute_balance(trip_id, db)` where db is the Firestore client from firebase_service.init_firebase(). The function returns the balance dictionary and also persists it to the trip document in Firestore.