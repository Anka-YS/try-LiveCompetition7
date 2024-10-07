import os
import subprocess
# venv環境を指定
conda_env = "lc7"
# 実行するスクリプトを指定
sub = [
    "tin.py",
    "lllm_dialogue.py",
    "tout.py"
]
script_directory = os.path.dirname(os.path.abspath(__file__))

cmd_template = f"cd /d {script_directory}\\modules && conda activate {conda_env} && echo Running {{cmd}} && python {{cmd}}"
for command in sub:
    print(command)
    full_command = f"start cmd /k \"{cmd_template.format(cmd=command)}\""
    print(f"Executing: {full_command}")
    subprocess.Popen(full_command, shell=True)


# GUIの実行
post_script_command = f"cd /d {script_directory}\\MMDAgent-EX && cscript run.vbs"
print(f"{post_script_command}")
subprocess.Popen(post_script_command, shell=True)