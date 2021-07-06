import requests
import json
from os import environ
from locale import LC_ALL, setlocale
from fortifyapi.fortify import FortifyApi

print("Reading settings file...")
try:
    f = open('settings.json')
    settings = json.load(f)
    f.close()
except Exception as e:
    print(e)
    print("Error reading settings file")
    sys.exit(0)

 # Authenticate and retrieve token
def token():
     api = FortifyApi(host=url, username=user, password=password, verify_ssl=False)
     response = api.get_token(description=description)
     return response.data['data']['token']

 # Set vars for connection
url = settings['SSC_URL']
user = settings['username']
password = settings['password']
description = settings['description']
token = token()
 # Re-use token in all requests
def api():
     api = FortifyApi(host=url, token=token, verify_ssl=False)
     return api

 # List ID, Project/application Version
def list():
     response = api().get_all_project_versions()
     data = response.data['data']
     for version in data:
         print("{0:8} {1:30} {2:30}".format(version['id'], version['project']['name'], version['name']).encode(
             'utf-8', errors='ignore').decode())
             
 # Deletes user via a DELETE request
def delete_user():
    query = input("Enter the username or email to be deleted (Ex: asrey): " )
    user_id_response = api().get_ldap_user(query)
    count = user_id_response.data['count']
  
    if(count == 0):
        print("User not found. Please try again.")
        exit()
    elif(count == 1):
        #Deletes the user
        userId = user_id_response.data['data'][0]['id']
        name = user_id_response.data['data'][0]['name']
        response = api().delete_ldap_user(userId)   
        print("Success! User: " +name +" has been deleted.")
    elif(count > 1):
        #If non-unique information is passed in the user is prompted with all the found users and asked to try again
        count_users = 0
        multiple_user_response = user_id_response.data['data']
        print("These users were found: ")
        for names in multiple_user_response:
            print(user_id_response.data['data'][count_users]['name'] + 
            " (" + user_id_response.data['data'][count_users]['firstName'] + " " 
            + user_id_response.data['data'][count_users]['lastName'] +")" ) 
            count_users+=1
        print("Please retry and enter the unique Deloitte ID or email.")
        exit()
    else:
        print("Error. Please ensure the credentials are correct.")
        exit()
   
        
def get_user():
    response = api().get_ldap_user("robert")
    print(response.data_json())
    
def get_ldap_user_from_id():
    response = api().get_ldap_user_from_id(0)
    print(response.success)
    
def get_unregistered_user():
    response = api().get_unregistered_user("")
    print(response.message)

# Updates LDAP user to a new role 
def update_ldap_user():
# Prompts the user for username and desired new role
    query = input("Enter the username or email (Ex: asrey): ")
    newRole = input("Enter the new role (Ex: MF Developer): ")
    new_role_id = -1
    user_data_response = api().get_ldap_user(query)
    if(user_data_response.success == False):
        print("An error occurred. Please ensure the userId is correct.")
        exit()
    
    if(user_data_response.data['count'] == 1):
        distinguishedName = user_data_response.data['data'][0]['distinguishedName']
        userId = user_data_response.data['data'][0]['id']
        email = user_data_response.data['data'][0]['email']
        firstName = user_data_response.data['data'][0]['firstName']
        lastName = user_data_response.data['data'][0]['lastName']
        ldapType = user_data_response.data['data'][0]['ldapType']
        name = user_data_response.data['data'][0]['name']
        role_name = user_data_response.data['data'][0]['roles'][0]['name']
        role_description = user_data_response.data['data'][0]['roles'][0]['description']
        objectVersion = user_data_response.data['data'][0]['roles'][0]['objectVersion']
        publishVersion = user_data_response.data['data'][0]['roles'][0]['publishVersion']
        
    elif(user_data_response.data['count'] > 1):
    #If non-unique information is passed in the user is prompted with all the found users and asked to try again
        count = 0
        multiple_user_response = user_data_response.data['data']
        print("These users were found: ")
        for names in multiple_user_response:
            print(user_data_response.data['data'][count]['name'] + 
            " (" + user_data_response.data['data'][count]['firstName'] + " " 
            + user_data_response.data['data'][count]['lastName'] +")" ) 
            count+=1
        print("Please retry and enter the unique Deloitte ID or email.")
        exit()
        
    else:
        print("An error occurred, the user could not be found.")
        exit()
        
    roles_response =  api().get_roles_list()
    role_data = roles_response.data['data']
  
  #Finds the role id associated with the role name passed in
    for names in role_data:
        if(names['name'] == newRole):
           new_role_id = names['id']
           break
           
    if(new_role_id == -1):
        print("Error! Role not found.")
        exit()
        
    final_response = api().update_ldap_user_role(userId, distinguishedName, email, firstName, 
    lastName, ldapType, name, role_description, new_role_id, newRole, objectVersion, publishVersion) 
    
    #Double checks to ensure that the update was sucessful and the database has the correct role saved
    
    #This check has been commented out for speed purposes (querying the test environment is very slow), may be added back later
    
    #successCheck = api().get_ldap_user(query)
    #successCheck_data = successCheck.data['data'][0]['roles'][0]['name']
    #if(successCheck_data == newRole):
    print("Success! " + name + " has been updated to the " + '"' + newRole + '" ' + "role.")
    #else:
        #print("An error occurred. Please retry the request and ensure the input is correct.")


def delete_all_tokens():
    response = api().delete_all_user_tokens()
    print(response.message)

def create_ldap_user():
    response = api().set_ldap_user("CN=Mitchell\\, Alex [alemitchell],OU=Users,OU=Adelaide,OU=SA,OU=State,OU=Production,DC=au,DC=deloitte,DC=com", "")
    print(response.data_json(pretty = True))

if __name__ == '__main__':

     print("Please press the associated number for the desired action: \n")
     print("1. Update an LDAP User role\n")
     print("2. Delete a LDAP User\n")
     query = input()
     
     if(query == "1"):
        update_ldap_user()
     elif(query == "2"):
        delete_user()
     else:
        print("Please try again with a valid choice.")
      