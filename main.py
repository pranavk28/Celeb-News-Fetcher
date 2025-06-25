from celebnews import fetch_and_summarize

def main():
    name = input("Enter celebrity name: ").strip()
    count = input("Articles to fetch [5]: ").strip()
    count = int(count) if count.isdigit() else 5

    use_filter = input("Filter by recency? (y/N): ").lower() == "y"
    if use_filter:
        date_value = int(input("  Number of units (e.g. 7): ").strip())
        date_unit  = input("  Unit (day, week, month): ").strip().lower()
        summary = fetch_and_summarize(name, count, date_value, date_unit)
    else:
        summary = fetch_and_summarize(name, count)

    print("\n" + summary)

if __name__ == "__main__":
    main()
