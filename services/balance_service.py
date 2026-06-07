from collections import defaultdict

def recompute_balance(trip_id: str, db) -> dict:
    """
    Recompute the balance for a trip based on its entries.

    Args:
        trip_id: The ID of the trip document
        db: Firestore client instance

    Returns:
        dict: Balance dictionary with user IDs as keys and net amounts as values
              (positive means they are owed money, negative means they owe money)
    """
    # Fetch all entries from trips/{tripId}/entries subcollection
    entries_ref = db.collection("trips").document(trip_id).collection("entries")
    entries = entries_ref.stream()

    # Sum amounts per paidByUid using a plain dict
    paid_by = defaultdict(float)
    for entry in entries:
        entry_data = entry.to_dict()
        amount = entry_data.get("amount", 0)
        paid_by_uid = entry_data.get("paidByUid")
        if paid_by_uid:
            paid_by[paid_by_uid] += amount

    # Convert to regular dict for easier handling
    paid_by = dict(paid_by)

    # Handle edge case: no entries
    if not paid_by:
        balance_dict = {}
        # Still update the trip document with empty balance
        db.collection("trips").document(trip_id).update({"balance": balance_dict})
        return balance_dict

    # Calculate total spent and fair share (assuming 2 users as per instructions)
    total_spent = sum(paid_by.values())
    fair_share = total_spent / 2.0

    # Compute balance for each user: what they paid minus what they should have paid (fair share)
    balance_dict = {}
    for uid, amount_paid in paid_by.items():
        balance_dict[uid] = amount_paid - fair_share

    # Write balance dict back to trips/{tripId} document
    db.collection("trips").document(trip_id).update({"balance": balance_dict})

    return balance_dict