from analysis.cause_classifier import classify_process
from analysis.confidence_engine import calculate_confidence
from analysis.bottleneck_detector import detect_bottleneck


def generate_root_cause_report(
    disk_usage_percent,
    top_processes,
    spike_detected=False,
    sustained_activity=False,
):
    """
    Generate a root cause analysis report.
    """

    bottleneck = detect_bottleneck(
        disk_usage_percent,
        top_processes
    )

    if not bottleneck["bottleneck_detected"]:
        return {
            "status": "NO_BOTTLENECK",
            "message": "No significant bottleneck detected."
        }

    process_name = bottleneck["likely_process"]

    process_share = 0

    for process in top_processes:
        if process["name"] == process_name:
            process_share = process["percentage"]
            break

    cause_info = classify_process(process_name)

    confidence = calculate_confidence(
        process_share=process_share,
        spike_detected=spike_detected,
        sustained_activity=sustained_activity,
    )

    evidence = [
        f"Disk usage reached {disk_usage_percent}%",
        (
            f"{process_name} consumed "
            f"{process_share}% of disk activity"
        ),
    ]

    if spike_detected:
        evidence.append(
            "Recent disk spike detected"
        )

    if sustained_activity:
        evidence.append(
            "Sustained disk activity observed"
        )

    recommendation_map = {
        "Windows Search Indexing":
            "Pause indexing temporarily.",
        "Windows Defender Scan":
            "Schedule scans during idle hours.",
        "Browser Activity":
            "Reduce active tabs and extensions.",
        "Development Environment Activity":
            "Close unused projects and tools.",
        "Python Script Activity":
            "Review script disk access patterns.",
        "Windows Background Service":
            "Investigate active Windows services.",
        "Unknown Activity":
            "Perform deeper process analysis."
    }

    return {
        "status": "BOTTLENECK_DETECTED",
        "severity": bottleneck["severity"],
        "process": process_name,
        "cause": cause_info["cause"],
        "category": cause_info["category"],
        "confidence": confidence,
        "evidence": evidence,
        "recommendation": recommendation_map.get(
            cause_info["cause"],
            "Further investigation required."
        ),
    }


def print_root_cause_report(report):
    """
    Print report in a readable format.
    """

    print("\nROOT CAUSE ANALYSIS")
    print("=" * 60)

    if report["status"] != "BOTTLENECK_DETECTED":
        print(report["message"])
        return

    print(f"Cause        : {report['cause']}")
    print(f"Process      : {report['process']}")
    print(f"Category     : {report['category']}")
    print(f"Severity     : {report['severity']}")
    print(f"Confidence   : {report['confidence']}%")

    print("\nEvidence")
    print("-" * 60)

    for item in report["evidence"]:
        print(f"- {item}")

    print("\nRecommendation")
    print("-" * 60)
    print(report["recommendation"])


if __name__ == "__main__":

    sample_processes = [
        {
            "name": "SearchIndexer.exe",
            "percentage": 42.5
        },
        {
            "name": "chrome.exe",
            "percentage": 18.2
        }
    ]

    report = generate_root_cause_report(
        disk_usage_percent=97,
        top_processes=sample_processes,
        spike_detected=True,
        sustained_activity=True,
    )

    print_root_cause_report(report)
