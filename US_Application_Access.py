import requests
import json
import sys
import signal
import getpass
import collections
from os import environ
from locale import LC_ALL, setlocale
from fortifyapi.fortify import FortifyApi
from sys import exit

print("Reading settings file...")
try:
    f = open('settings.json')
    settings = json.load(f)
    f.close()
except Exception as e:
    print(e)
    print("Error reading settings file")
    sys.exit(0)

#print("Please enter your FortifySSC credentials:\n")

username = input("Username:")
password = getpass.getpass()


 # Authenticate and retrieve token
def token_creation():
     api = FortifyApi(host=url, username=username, password=password, verify_ssl=False)
     response = api.get_token(description=description)
     if(response.success == False):
        print("Incorrect credentials, please try again.")
        exit()
     else:
        #tokenId = response.data['data']['id']
        return [response.data['data']['token'], response.data['data']['id']]



# Set vars for connection
url = settings['SSC_URL']
user = username
password = password
description = settings['description']
token_dict = token_creation()
token = token_dict[0]
tokenId = token_dict[1]




 # Re-use token in all requests
def api():
     api = FortifyApi(host=url, token=token, verify_ssl=False)
     return api
     
# Creates a api object with basic authentication to be used for deleting tokens associated with the user     
def api_delete_token():
    delete_token_api = FortifyApi(host=url, username=username, password=password, verify_ssl=False)
    return delete_token_api

def delete_singular_token(token_Id):
    delete_response = api_delete_token().delete_token(token_Id)
    if(delete_response.message == 'OK'):
        print("Token has been deleted.")
    else:
        print("There was an error. Please check FortifySSC to ensure the token has been deleted")
        
def update_ldap_version():
    
    while True:
        print("Enter quit to exit and delete token")
        query = input("Enter the username or email (Ex: asrey): ")
        if(query == ''):
            print("Error! Empty string detected. Please retry.")
            main()
        if(query == 'quit'):
            delete_singular_token(tokenId)
            exit()
        user_data_response = api().get_ldap_user(query)
        #If only one user is found, userId of that user is stored
        if(user_data_response.data['count'] == 1):
            firstName = user_data_response.data['data'][0]['firstName']
            lastName = user_data_response.data['data'][0]['lastName']
            role_name = user_data_response.data['data'][0]['roles'][0]['name']
            name = user_data_response.data['data'][0]['name']
            print("User found: " + name + " " + "(" + firstName + ", " + lastName + ")")
            print("Current role: " + role_name)
            userId = user_data_response.data['data'][0]['id']
            response = api().get_ldap_user_versions(userId)
            idx = 0
            project_names_list = response.data['data']
             
            #print(response.data_json(pretty = True))
            #print(project_names_list)
            print("Current Versions:")
            for names in project_names_list:
                print(response.data['data'][idx]['project']['name'] + " - " + response.data['data'][idx]['name'])
                idx+=1
            print("\n")
            break
        
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
            
        else:
            print("An error occurred, the user could not be found. Please retry with the correct Deloitte credentials")
          
    
    while True:
    #Prompts user for desired Application Name
        print("Enter quit to exit and delete the token")
        application_name = input("Enter Application Header (Ex: AU, US, KR): ")
        #Typing quit allows the user to return to the main menu
        if(application_name == 'quit'):
            print("Quitting...")
            delete_singular_token(tokenId)
            exit()
            
        project_name = api().get_project_versions(application_name)
        
        #If project could not be found, user is prompted to try again
        if(project_name.data['count'] == 0):
            project_list = api().get_projects(application_name)
            print("Error! Specific project could not be found or application does not have any active versions.")
        #Prints all the found applications based on the users query    
            idx = 0
            project_names_list = project_list.data['data']
            project_dict = {}
            for names in project_names_list:
                print(project_list.data['data'][idx]['name'])
                project_dict.update({idx: project_list.data['data'][idx]['name']})
                idx+=1
                
            #print(project_dict)
                
           
            provision_access_all(project_dict, userId)
            
def provision_access_all(project_dict, userId):
    for project in project_dict:
        count = 1
        idx = 0
        project_name = api().get_project_versions(project_dict.get(project))
        multiple_project_response = project_name.data['data']
        #Finds and prints the versions associated with the application
        print(project_dict.get(project))
        print("These project versions were found: ")
        select_dict = {}
        for names in multiple_project_response:
            select_dict.update({project_name.data['data'][idx]['name']: project_name.data['data'][idx]['currentState']['id']})
            print(str(count) + ". " + project_name.data['data'][idx]['name'])
            count+=1
            idx+=1
 
        #break
            
        for versions in select_dict:
            add_version = api().add_project_version(userId, select_dict.get(versions))
            print(project_dict.get(project) + ": " + versions)
            if(add_version.message == 'OK'):
                print("Success! " + versions + " has been added.")
            else:
                print("Error! " + versions + " could not be added.")
            
                            
        
   
                        
            
if __name__ == '__main__':
    update_ldap_version()