"""
Convert numeric amount to words for Pakistani Rupees (FBR invoice requirement)
"""

ONES = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
        'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
        'Seventeen', 'Eighteen', 'Nineteen']
TENS = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']


def _to_words_under_1000(n):
    if n == 0:
        return ''
    if n < 20:
        return ONES[n]
    if n < 100:
        return (TENS[n // 10] + ' ' + ONES[n % 10]).strip()
    return (ONES[n // 100] + ' Hundred ' + _to_words_under_1000(n % 100)).strip()


def amount_to_words_pkr(amount):
    """
    Convert amount (number or string) to words for Pakistani Rupees.
    Returns e.g. "Thirty Nine Thousand Three Hundred Twenty Five Rupees Only"
    """
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return "Zero Rupees Only"
    if amount < 0:
        return "Minus " + amount_to_words_pkr(-amount)
    whole = int(amount)
    if whole == 0:
        return "Zero Rupees Only"
    if whole >= 10**12:
        return str(amount) + " Rupees Only"
    # Lakh = 100,000, Crore = 10,000,000
    words = []
    if whole >= 10**7:  # Crores
        words.append(_to_words_under_1000(whole // 10**7) + " Crore")
        whole %= 10**7
    if whole >= 10**5:  # Lakhs
        words.append(_to_words_under_1000(whole // 10**5) + " Lakh")
        whole %= 10**5
    if whole >= 10**3:  # Thousands
        words.append(_to_words_under_1000(whole // 10**3) + " Thousand")
        whole %= 10**3
    if whole:
        words.append(_to_words_under_1000(whole))
    result = " ".join(words).strip() + " Rupees Only"
    return result
