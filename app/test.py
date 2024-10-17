import requests
from pprint import pprint
import json

def main():
    url = 'https://api.sandbox.vm.co.mz:18345/ipg/v1x/b2cPayment/'
    
    token="XfsLebYAsnNPRsMu6JKfRPH9W5fhzSb+W3cdizVQ/Bm5ho2Xi/tn/Oo4bwHmFLqYlHQVnrog3MziMmxZLN5NnPEqCu5F9tLeYwmIo4mqNp544Ai5B8s+IAbxr//WLIS+pk992fp6uZl8IgFkQreqsN+leWSgQdeW7oiGl7Z5k6e10uc4xuD3KOEldtye0Pzjj0DmHNdhDh8SzpdgkjyEmWPhvyMwCVxn80pqaKAH5UUDGxv+dbY4HgsoAprMC+hclhHkVfk5VfqNlOToxpn6LmfeoZZ5BJJysEA/Y/T3zlK9JYq+dWahlWyMv+UoMEh7VG1lw3k/Hb7dqKkSRmrhStsuRrHjAITKRSoWv98ZWntQQua+Fz/BGV7v6f6qsytTBHCWVJD3qWl3phKztYWpr0CeJ3aGYns+gtKP04V2WdPrqVylYJFEQILGCfKmtFqYZ3rhdKhgs4UDAOQMCkED4uS+op0p+I6kW6ftAyw6WDu5dqQ5OFKV3++f/015kptDzRpoieB1EfUltgabnfWCNzivi7ZJY6S+5+ZJPDI9ORjYq+QlF+Qi/RQmJiGWDh+S/UY2sA2d9692lfmWKk3+10YAUoZlQTlq9qCvqVXYVwquiLkUpHhnpNMbidVBwuBM03IxA0SrmervTM7RY2mS1BXTwO2IQekX+9bnJ6+Tpkk="
    headers = {
           "Content-Type": "application/json",
           "Authorization": f"Bearer {token}",
           "Origin": "developer.mpesa.vm.co.mz"
    }
    
    # Parâmetros da requisição
    data = {
        'input_TransactionReference': 'T12344C',
        'input_CustomerMSISDN': '258843330333',
        'input_Amount': '10',
        'input_ThirdPartyReference': '111PA2D',
        'input_ServiceProviderCode': '171717'
    }
    
    # Fazendo a requisição POST
    response = requests.post(url, headers=headers,verify=True, data=json.dumps(data))
    
    # Exibindo o resultado da requisição
    pprint(response.status_code)
    pprint(response.headers)
    pprint(response.json())  # Caso o conteúdo da resposta seja em formato JSON

if __name__ == '__main__':
    main()
