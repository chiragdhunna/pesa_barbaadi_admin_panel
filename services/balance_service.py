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
        amount = float(entry_data.get("amount", 0) or 0)  # fix: cast to float, guard None
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

    # Write both Schema B (uid -> amount) and Schema A (owedTo, owedBy, amount) back to Firestore
    owed_to = None
    owed_by = None
    net_amount = 0.0

    for uid, bal in balance_dict.items():
        if bal > 0:
            owed_to = uid
            net_amount = bal
        elif bal < 0:
            owed_by = uid

    if owed_to and owed_by:
        balance_dict['owedTo'] = owed_to
        balance_dict['owedBy'] = owed_by
        balance_dict['amount'] = net_amount

    # Write balance dict back to trips/{tripId} document
    db.collection("trips").document(trip_id).update({"balance": balance_dict})

    return balance_dict

def parse_balance(balance: dict) -> tuple:
    """
    Parses a balance dictionary from Firestore and returns (owed_by, owed_to, amount_owed).
    Supports both Schema A (mobile client: owedBy, owedTo, amount) and
    Schema B (admin: uid -> net_amount).
    """
    if not balance:
        return None, None, 0.0

    # 1. Try mobile client Schema A
    if 'owedBy' in balance or 'owedTo' in balance or 'amount' in balance:
        owed_by = balance.get('owedBy')
        owed_to = balance.get('owedTo')
        try:
            amount_owed = float(balance.get('amount', 0.0))
        except (TypeError, ValueError):
            amount_owed = 0.0
        return owed_by, owed_to, amount_owed

    # 2. Try admin Schema B (uid -> net_amount)
    owed_to = None
    owed_by = None
    amount_owed = 0.0

    for uid, amount in balance.items():
        try:
            amount_val = float(amount)
        except (TypeError, ValueError):
            continue
        if amount_val > 0:
            owed_to = uid
            amount_owed = amount_val
        elif amount_val < 0:
            owed_by = uid

    return owed_by, owed_to, amount_owed