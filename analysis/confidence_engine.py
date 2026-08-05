PROCESS_SHARE_WEIGHT = 0.50
SPIKE_WEIGHT = 0.30
SUSTAINED_ACTIVITY_WEIGHT = 0.20


def calculate_confidence(
    process_share,
    spike_detected=False,
    sustained_activity=False,
):
    """
    Calculate confidence score for a suspected root cause.
    """

    score = 0.0

    # Process contribution
    process_score = min(process_share, 100) / 100
    score += process_score * PROCESS_SHARE_WEIGHT

    # Recent spike
    if spike_detected:
        score += SPIKE_WEIGHT

    # Sustained activity
    if sustained_activity:
        score += SUSTAINED_ACTIVITY_WEIGHT

    confidence = round(score * 100, 2)

    return min(confidence, 100.0)


if __name__ == "__main__":

    confidence = calculate_confidence(
        process_share=42,
        spike_detected=True,
        sustained_activity=True,
    )

    print("Confidence Score")
    print("=" * 40)
    print(f"Confidence: {confidence}%")
