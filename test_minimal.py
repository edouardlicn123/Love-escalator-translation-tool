
def init_db():
    print("init_db running")

print("Before load_config")
load_config()
print("After load_config")
init_db()
print("After init_db")

def load_config():
    print("load_config running")
