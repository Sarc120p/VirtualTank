from pymodbus.client.sync import ModbusTcpClient

client = ModbusTcpClient("127.0.0.1", port=5020)
print("A tentar ligar ao simulador em 127.0.0.1:5020...")
if client.connect():
    print("Ligacao OK.")
    resultado = client.read_holding_registers(0, 10)
    if resultado.isError():
        print("Erro na leitura dos registos.")
        print("Detalhes do erro:", resultado)
    else:
        print("Valores dos registos:", resultado.registers)
    client.close()
else:
    print("Falha na ligacao. Verifica se o simulador esta a correr e a porta 5020 nao esta bloqueada.")