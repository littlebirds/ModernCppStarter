#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

TEMPLATE_PROJ_NAME = "Greeter"


def replace_inplace(file_path, old, new):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
    except Exception as e:
        print(f"Skipping file {file_path} due to encoding issues.")
        return 0
    occurrences = content.count(old)
    if occurrences > 0:
        content = content.replace(old, new)
        with open(file_path, 'w') as file:
            file.write(content)
    return occurrences


def update_cmakelists(old_name, new_name):
    assert old_name != new_name, "Old and new project names must be different."
    print(f"Rename project from '{old_name}' to '{new_name}' in CMakeLists.txt files ...")
    files_processed = 0
    replacements_total = 0
    for root, _, files in os.walk('.'):
        for file in files:
            if file == "CMakeLists.txt":
                path = os.path.join(root, file)
                replacements = replace_inplace(path, old_name, new_name)
                if replacements > 0:
                    files_processed += 1
                    replacements_total += replacements
    print("\nSummary:")
    print(f"Total CMakeLists.txt files processed: {files_processed}")
    print(f"Total replacements made: {replacements_total}")
    return files_processed 


def update_includes(old_name, new_name):
    print("Updating include directory and includes ...")
    old_lower = old_name.lower()
    new_lower = new_name.lower()
    old_include = os.path.join("include", old_lower)
    new_include = os.path.join("include", new_lower)
    if os.path.exists(old_include):
        shutil.move(old_include, new_include)

    for root, _, files in os.walk('.'):
        if root == '.git':
            continue
        for file in files:
            if file.endswith(('.cpp', 'cxx', '.h', '.hpp')):
                path = os.path.join(root, file)
                replace_inplace(path, f"#include <{old_lower}/", f"#include <{new_lower}/")
    

def update_version_test(old_name, new_name):
    print("Updating project version testing ...")
    old_upper = old_name.upper()
    new_upper = new_name.upper()
    for root, _, files in os.walk('.'):
        if root == '.git':
            continue
        for file in files:
            path = os.path.join(root, file)
            replace_inplace(path, f"{old_upper}_VERSION", f"{new_upper}_VERSION")

def buid_test(new_name):
    print("Verifying that the porject builds and runs tests ...")
    subprocess.run(["cmake", "-S", "all", "-B", "build"], check=True)
    subprocess.run(["cmake", "--build", "build"], check=True)
    subprocess.run([f"./build/test/{new_name}Tests"], check=True)
    subprocess.run(["cmake", "--build", "build", "--target", "fix-format"], check=True)
    subprocess.run([f"./build/standalone/{new_name}", "--help"], check=True)
    # subprocess.run(["cmake", "--build", "build", "--target", "GenerateDocs"], check=True)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <new_project_name>")
        print(f"Example: {sys.argv[0]} MyProject")
        sys.exit(1)
    new_proj_name = sys.argv[1]
    file_changed = update_cmakelists(TEMPLATE_PROJ_NAME, new_proj_name)
    if file_changed == 0:
        print("This project seems to be already renamed.")
        sys.exit(0)
    update_includes(TEMPLATE_PROJ_NAME, new_proj_name)
    update_version_test(TEMPLATE_PROJ_NAME, new_proj_name)
    try:
        buid_test(new_proj_name)
        subprocess.run(['rm', '-rf', 'build'])
        subprocess.run(['rm', '-rf', '.git'])
        subprocess.run(['git', 'init'])
        subprocess.run(['git', 'add', '--all'])
        subprocess.run(['git', 'commit', '-m', 'initialize git repoistory'])
        subprocess.run(['git', 'branch', '-m', 'main'])
    except subprocess.CalledProcessError as e:
        print(f"Error during build or test: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
