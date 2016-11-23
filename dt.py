from datetime import datetime
t = datetime.now().time().strftime("%H%M%S")
f = "keres"+t+".txt"
print(f)
