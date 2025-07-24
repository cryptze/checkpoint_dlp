import re

pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
text = "test@test.com"

if re.search(pattern, text, re.IGNORECASE):
    print("Detectado: El texto contiene un correo electrónico.")
else:
    print("No detectado: El texto no contiene un correo electrónico.")
