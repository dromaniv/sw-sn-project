import os
import re

def split_txt_files(input_directory):
    # Regular expression to match headings like == Title ==
    heading_pattern = re.compile(r'^==\s*(.+?)\s*==$', re.MULTILINE)

    # Iterate over all .txt files in the input directory
    for filename in os.listdir(input_directory):
        if filename.lower().endswith('.txt'):
            file_path = os.path.join(input_directory, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Split the content based on the heading pattern
            sections = heading_pattern.split(content)

            # The split will result in a list where even indices are content before the first heading
            # and odd indices are the headings. We'll pair them accordingly.
            # Example: [pre_content, heading1, section1, heading2, section2, ...]

            # Initialize a list to hold (heading, section) tuples
            paired_sections = []

            # Start from index 1 to skip any pre_content before the first heading
            for i in range(1, len(sections), 2):
                heading = sections[i].strip()
                section = sections[i + 1].strip()
                if section:  # Only add non-empty sections
                    paired_sections.append((heading, section))

            if paired_sections:
                # Create a directory named after the initial txt file (without extension)
                base_filename = os.path.splitext(filename)[0]
                output_dir = os.path.join(input_directory, base_filename)
                os.makedirs(output_dir, exist_ok=True)

                # Save each section as a separate txt file
                for idx, (heading, section) in enumerate(paired_sections, start=1):
                    output_filename = f"{base_filename}{idx}.txt"
                    output_path = os.path.join(output_dir, output_filename)
                    with open(output_path, 'w', encoding='utf-8') as out_file:
                        # Optionally, you can include the heading in the new file
                        out_file.write(f"== {heading} ==\n\n{section}")
                print(f"Processed '{filename}' into {len(paired_sections)} sections.")
            else:
                print(f"No sections found in '{filename}'.")

if __name__ == "__main__":
    # Specify the directory containing your .txt files
    input_dir = input("Enter the path to the directory containing the .txt files: ").strip()
    # deafault path, just click enter
    if input_dir == "":
        input_dir = "sw-sn-project/data"

    if not os.path.isdir(input_dir):
        print("The provided path is not a valid directory.")
    else:
        split_txt_files(input_dir)
        print("All files have been processed.")
