from flask import Flask, request, jsonify, render_template
import subprocess
import os
import uuid
import sys

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/run', methods=['POST'])
def run_code():
    data = request.get_json()

    code = data.get('code')
    user_input = data.get('input', '')
    language = data.get('language')

    if not code:
        return jsonify({"error": "No code provided"}), 400

    unique_id = uuid.uuid4().hex

    try:
        # ================= PYTHON =================
        if language == "python":
            filename = f"temp_{unique_id}.py"

            with open(filename, "w") as f:
                f.write(code)

            result = subprocess.run(
                [sys.executable, filename],
                input=user_input,
                capture_output=True,
                text=True,
                timeout=5
            )

            output = result.stdout
            error = result.stderr

            if os.path.exists(filename):
                os.remove(filename)

        # ================= C =================
        elif language == "c":
            c_file = f"temp_{unique_id}.c"
            exe_file = f"temp_{unique_id}"

            # Windows fix
            if os.name == "nt":
                exe_file += ".exe"

            with open(c_file, "w") as f:
                f.write(code)

            # Compile
            compile_result = subprocess.run(
                ["gcc", c_file, "-o", exe_file],
                capture_output=True,
                text=True
            )

            if compile_result.returncode != 0:
                return jsonify({"error": compile_result.stderr})

            # Run
            if os.name == "nt":
                run_command = [exe_file]
            else:
                run_command = ["./" + exe_file]

            run_result = subprocess.run(
                run_command,
                input=user_input,
                capture_output=True,
                text=True,
                timeout=5
            )

            output = run_result.stdout
            error = run_result.stderr

            # Cleanup
            if os.path.exists(c_file):
                os.remove(c_file)
            if os.path.exists(exe_file):
                os.remove(exe_file)

        else:
            return jsonify({"error": "Unsupported language"})

        return jsonify({
            "output": output.strip(),
            "error": error.strip()
        })

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timed out!"})

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)