import os
import subprocess

from roundtable.shared.utils.logger import Logger


class GUI:
    def __init__(self):
        self.logger = Logger()
        self.interface_path = os.path.join(os.path.dirname(__file__), "interface.py")

    def show(self):
        self.logger.info("Showing GUI...")
        process = subprocess.Popen(["streamlit", "run", self.interface_path])
        output, error = process.communicate()
        p_status = process.wait()
        self.logger.debug(output)
        self.logger.debug(error)
