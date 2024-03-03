from roundtable.shared.utils.logger import Logger


class Meeting:
    def __init__(self):
        self.logger = Logger()

    def start_meeting(self):
        self.logger.info("Meeting started")
        running = True
        while running:
            user_input = input("Enter text (press 'q' or ctrl-c to quit): ")
            if user_input.lower() == 'q':
                running = False
            print(f"> {user_input}")
        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")

    def save_report(self):
        self.logger.info("Report saved")
        pass
