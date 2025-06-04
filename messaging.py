def message(tp: int, message: str):
    types = ["ERROR", "WARNING", "INFO"]
    
    print(f"[{types[tp]}] {message}")    
    return