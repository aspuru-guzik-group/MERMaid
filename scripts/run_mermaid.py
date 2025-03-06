import subprocess

def run_subprocess(module_name):
    """
    Runs a Python script as a subprocess.

    :param module_name: Name of the module to run.
    :type module_name: str
    :param args: List of command-line arguments to pass to the script (optional).
    :type args: list, optional
    :return: None
    """
    cmd = ["python", module_name]
    result = subprocess.run(cmd, capture_output=True, text=True)

    print(f"\n===== {module_name} Output =====\n")
    print(result.stdout)

    if result.stderr:
        print(f"\n===== {module_name} Errors =====\n")
        print(result.stderr)

def main():
    """
    Runs VisualHeist, DataRaider and KGWizard sequentially.

    :return: None
    """
    print("\n### Running VisualHeist ###\n")
    run_subprocess("scripts/run_visualheist.py")

    print("\n### Running DataRaider ###\n")
    run_subprocess("scripts/run_dataraider.py")

    # print("\n### Running KGWizard ###\n")
    # run_subprocess("scripts/run_kgwizard.py")

if __name__ == "__main__":
    main()
