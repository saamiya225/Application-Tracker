from src.workflow import process_inbox, run_auto_followups, run_pending_scheduled

def main():
    print("Processing inbox...")
    actions = process_inbox()

    if actions:
        print("Actions:", actions)
        run_auto_followups(actions)

    print("Checking scheduled follow-ups...")
    run_pending_scheduled()

if __name__ == "__main__":
    main()
