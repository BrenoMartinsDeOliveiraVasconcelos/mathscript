import re
import messaging
import stringmanip
import mathplus
import math

KEYWORDS = {
    "VAR": "variable",
    "INPUT_VAR": "variable",
    "SUM": "return_function",
    "SUB": "return_function",
    "MUL": "return_function",
    "DIV": "return_function",
    "OUTPUT": "print_function",
    "IF": "start_cond",
    "ENDIF": "end_cond",
    "INPUT" : "input_function",
    "END": "end_script",
    "LOOP": "loop",
    "ENDLOOP": "end_loop"
} # Keyword: type

REGEXES = {
    "arg_char": ",",
    "arg_sep": "(([A-z]|[0-9]){1,}([,]|)( |))",
    "output_to": "->",
    "variable_assign": "=",
    "variable_naming": "([A-z]([0-9]|)*){1,100}$"
}

MACROS = {
    "ENDLINE" : "\n"
}

CONDITIONS = ["<", ">", "==", "<=", ">=", "!=", "NUM", "NOT_NUM"]

EVENTS = ["variable_declaration", "function_call", "print", "conditional", "conditional_end", "input", "end_script", "loop", "end_loop"]


class Interpreter:
    def __init__(self, file: str):
        self.file = open(file, "r").readlines()
        self.variables = {}
        self.input_variables = {}
        self.current_line = 0
    
    
    def _exit(self, code):
        exit(code)
    

    # GEt line data    
    def _line_interpret(self, line: str, line_num: int, file: list) -> dict:
        index = 0
        for word in line.split(" "):
            word = stringmanip.sanitize(word)
                
            # Check if there's a keyword on first char
            if word in KEYWORDS.keys() and index == 0:
                tp = KEYWORDS[word]
                if tp == "variable":
                    # Check variable name
                    line_split = line.split(" ")
                    line_split_assign = line.split(REGEXES["variable_assign"])
                    if re.match(REGEXES["variable_naming"], line_split[1]) and len(line_split_assign) == 2:
                        try:
                            return_value = ""
                            if word != "INPUT_VAR":
                                return_value = float(line_split_assign[1])
                                self.variables[line_split[1]] = return_value
                            else:
                                return_value = stringmanip.sanitize(line_split_assign[1])
                                self.input_variables[line_split[1]] = return_value
                            return {
                                "event": EVENTS[0],
                                "variable": line_split[1],
                                "value": return_value
                            }
                        except ValueError:
                            messaging.message(0, f"Invalid variable value at line {line_num}")
                            self._exit(1)
                    else:
                        messaging.message(0, f"Invalid variable declaration at line {line_num}")
                        self._exit(1)    
                elif tp == "return_function":
                    line_split = line.split(REGEXES["output_to"])[0].split(word)[1]
                    
                    args = re.findall(REGEXES["arg_sep"], line_split)
                    
                    if not args:
                        messaging.message(0, f"Missing argument at line {line_num}")
                        self._exit(1)
                    
                    args_parsed = []
                    
                    for arg in args:
                        args_parsed.append(stringmanip.sanitize(arg[0].split(REGEXES["arg_char"])[0]))
                        
                    # Look for variables, if not check if number
                    values = []
                    output_var = stringmanip.sanitize(line.split(REGEXES["output_to"])[1])

                    if not output_var:
                        messaging.message(0, f"Missing output at line {line_num}")
                        self._exit(1)
                    
                    if output_var not in self.variables.keys():
                        messaging.message(0, f"Output variable is not defined before line {line_num}")
                        self._exit(1)
                    
                    for arg in args_parsed:
                        if arg not in self.variables.keys():
                            try:
                                values.append(float(arg))
                            except ValueError:
                                messaging.message(0, f"Invalid argument at line {line_num}")
                                self._exit(1)
                        else:
                            values.append(self.variables[arg])
                            
                    
                    # Do operation
                    if word == "SUM":
                        self.variables[output_var] = sum(values)
                    elif word == "SUB":
                        self.variables[output_var] = mathplus.sub_all(*values)
                    elif word == "MUL":
                        self.variables[output_var] = mathplus.mul_all(*values)
                    elif word == "DIV":
                        try:

                            self.variables[output_var] = mathplus.div_all(*values)
                        except ZeroDivisionError:
                            messaging.message(0, f"Division by zero is not allowed (line {line_num})")
                            self._exit(1)
                        
                    return {
                        "event": EVENTS[1],
                        "function": word,
                        "arguments": args_parsed,
                        "values": values,
                        "output": output_var,
                        "result": self.variables[output_var]
                    }
                # Receives only 1 arg, which is either a var or a string
                elif tp == "print_function":
                    arg = " ".join(line.split(" ")[1:])
                    arg = stringmanip.sanitize(arg)
                    output = arg
                    
                    if output in MACROS.keys():
                        output = MACROS[output]
                    
                    if output != "\n":
                        output += " "    
                    
                    if arg in self.variables.keys():
                        output = self.variables[arg]

                    print(output, end="", flush=True)
                        
                    return {
                        "event": EVENTS[2],
                        "argument": arg,
                        "output": output
                    }
                elif tp == "start_cond":
                    line_split = line.replace(word, "").split(" ")
                    
                    condition = {"value_1": stringmanip.sanitize(line_split[1]), "condition": line_split[2], "value_2": stringmanip.sanitize(line_split[3])}
                    
                    # Check if condition is on list
                    if condition["condition"] not in CONDITIONS:
                        messaging.message(0, f"Invalid conditional at line {line_num}")
                        self._exit(1)
                    
                    # Check if variables is either a var or a number
                    checks = [condition["value_1"], condition["value_2"]]
                    index = 0
                    for check in checks:
                        index += 1
                        if check not in self.variables.keys() and check not in self.input_variables.keys():
                            try:
                                condition[f"value_{index}"] = float(check) # type: ignore
                            except ValueError:
                                messaging.message(0, f"Invalid value '{check}' at line {line_num}")
                                self._exit(1)
                        else:
                            condition[f"value_{index}"] = self.variables[check] if check in self.variables.keys() else self.input_variables[check]
                    
                    # Look for end of condition
                    found = False
                    endif_line = line_num
                    for line in file[line_num:]:
                        endif_line += 1
                        if "ENDIF" in line:
                            found = True
                            break
                        
                    if not found:
                        messaging.message(0, f"Missing ENDIF for conditional at line {line_num}")
                        self._exit(1)
                        
                    
                    if endif_line - line_num < 2:
                        messaging.message(0, f"Expected instructions between lines {line_num} and {endif_line}")
                        self._exit(1)
                    
                    return {
                        "event": EVENTS[3],
                        "condition": condition,
                        "endif_line": endif_line
                    }
                elif tp == "end_cond":
                    return {
                        "event": EVENTS[4]
                    }
                elif tp == "input_function":
                    arg = " ".join(line.split(" ")[1:])
                    arg = stringmanip.sanitize(arg)
                    variable = ""
                    
                    if arg in self.variables.keys():
                        messaging.message(0, f"Variable '{arg}' is not inputable (line {line_num})")
                        self._exit(1)
                    elif arg in self.input_variables.keys():
                        variable = input()
                        self.input_variables[arg] = variable
                        
                        if mathplus.is_numeric(variable):
                            self.variables[arg] = float(variable)
                            variable = self.variables[arg]
                    
                    else:
                        messaging.message(0, f"Input variable '{arg}' is not defined before line {line_num}")
                        self._exit(1)
                    
                    return {
                        "event": EVENTS[5],
                        "argument": arg,
                        "input": variable
                    }
                elif tp == "end_script":
                    return {
                        "event": EVENTS[6]
                    }
                elif tp == "loop":
                    endloop = line_num
                    found = False
                    
                    for ln in file[line_num:]:
                        endloop += 1
                        if "ENDLOOP" in ln:
                            found = True
                            break
                        
                    if not found:
                        messaging.message(0, f"Missing ENDLOOP for loop at {line_num}")
                        self._exit(1)
                    
                    return {
                        "event": EVENTS[7],
                        "endloop": endloop
                    }
                elif tp == "end_loop":
                    return {
                        "event": EVENTS[8]
                    }
                else:
                    return {
                        "event": "NULL"
                    }
                        
            else:
                if line not in ["\n", ""]:
                    messaging.message(0, f"Missing valid instruction at line {line_num}")
                    self._exit(1)
                else:
                    return {
                        "event": "NULL"
                    }
                
            index += 1
            
            
    def run(self, debug: bool = False, lines: list[str] = [], use_global_linecount: bool = True):
        run_at = 0
        if len(lines) == 0 and use_global_linecount:
            lines = self.file            
        
        line_num = self.current_line
        
        if not use_global_linecount:
            line_num = 0
            
        for line in lines:
            line_num += 1
            
            if self.current_line > line_num:
                continue
            
            if run_at < line_num:  
                run_at += 1
                
            debug_str = f"\nLine: {line_num}\nRun at: {run_at}"
            line_info = {}
            
            if not line_num < run_at:
                line_info = self._line_interpret(line, line_num, lines)
            
            debug_str += f"\nAction: {line_info}"
            if debug:
                print(debug_str)
                
            if "event" not in line_info.keys():
                continue
            
            event = line_info["event"]
            
            if event == "NULL":
                continue
            
            if event == "conditional":
                condition = line_info["condition"]
                
                value_1 = condition["value_1"]
                value_2 = condition["value_2"]
                check_condition = CONDITIONS.index(condition["condition"])
                
                got_true = False
                
                if check_condition == 0:
                    got_true = value_1 < value_2
                elif check_condition == 1:
                    got_true = value_1 > value_2
                elif check_condition == 2:
                    got_true = value_1 == value_2
                elif check_condition == 3:
                    got_true = value_1 <= value_2
                elif check_condition == 4:
                    got_true = value_1 >= value_2
                elif check_condition == 5:
                    got_true = value_1 != value_2
                elif check_condition == 6:
                    got_true = mathplus.is_numeric(value_1)
                elif check_condition == 7:
                    got_true = not mathplus.is_numeric(value_1)
                
                if not got_true:
                    run_at = line_info["endif_line"]
                    continue
                
            if event == "end_script":
                return
            
            if event == "loop":
                begining = self.current_line + 1
                ending = line_info["endloop"] - 1
                run = []
                for line in lines[begining:ending]:
                    run.append(stringmanip.sanitize(line))
                
                if len(run) > 0:
                    try:
                        while run[-1] in ["LOOP", "ENDLOOP"]:
                            del run[-1]
                    except IndexError:
                        pass
                
                self.run(debug, run, False)
                self.current_line = ending + 1
                
            
            if use_global_linecount:
                self.current_line = line_num
                    
                
if __name__ == '__main__':
    test = Interpreter("test.txt")
    test.run(True)
