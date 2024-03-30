import requests

import logging
import logging.config

import sqlalchemy
from sqlalchemy.orm import sessionmaker

import uuid

import jwt

from os import path

from config.app_conf import app_conf
from models.asset import Asset
from models.asset_class import AssetClass,AssetClassMembership
from models.attribute import Attribute,AttributeType
from models.relation import Relation,RelationType


def _login(node_conf):
    uri = 'https://'+node_conf['source_node']+'/'+node_conf['tenant']+'/user_service/login'
    userID = node_conf['user']
    secret = node_conf['secret']
    Token = None
    response = requests.post(uri,data={'UserID':userID,'Secret':secret})
    logging.info(userID+','+node_conf['tenant']+':Logging in')
    if response.status_code == 200:
        data = response.json()
        for tenant in data['Tenants']:
            with open('/tmp/'+userID+'_'+tenant['baseid']+'_access.token','w') as token_file:
                token_file.write(tenant['access_token'])
            with open('/tmp/'+userID+'_'+tenant['baseid']+'_refresh.token','w') as token_file:
                token_file.write(tenant['refresh_token'])
            if tenant['baseid'] == node_conf['tenant']:
                Token = tenant['access_token']
    else: 
        logging.error(userID+','+node_conf['tenant']+':Login request failed with: '+str(response.status_code))
    return Token

def _refresh(node_conf,token):
    uri = 'https://'+node_conf['source_node']+'/'+node_conf['tenant']+'/user_service/refresh'
    userID = node_conf['user']
    Token = None
    response = requests.post(uri,headers={'Authorization':'Bearer '+token})
    logging.info(userID+','+node_conf['tenant']+':Refreshing')
    if response.status_code == 200:
        tenant = response.json()
        with open('/tmp/'+userID+'_'+node_conf['tenant']+'_access.token','w') as token_file:
            token_file.write(tenant['access_token'])
        Token = tenant['access_token']
    else: 
        logging.error(userID+','+node_conf['tenant']+':Refresh request failed with: '+str(response.status_code))
        Token = _login(node_conf)
    return Token

def _getAuthToken(node_conf):
    userID = node_conf['user']
    secret = node_conf['secret']
    access_path = '/tmp/'+userID+'_'+node_conf['tenant']+'_access.token'
    Token = None
    if path.exists(access_path):
        logging.info(userID+','+node_conf['tenant']+':Stored Access Token found')
        with open(access_path,'r') as token_file:
            token_from_file = token_file.read()
        try:
            jwt.decode(token_from_file,options={'verify_signature':False})
        except jwt.ExpiredSignatureError:
            pass
        else:
            return token_from_file
    refresh_path = '/tmp/'+userID+'_'+node_conf['tenant']+'_refresh.token'
    if path.exists(refresh_path):
        logging.info(userID+','+node_conf['tenant']+':Stored Refresh Token found')
        with open(refresh_path,'r') as token_file:
            token_from_file = token_file.read()
        try:
            jwt.decode(token_from_file,options={'verify_signature':False})
        except jwt.ExpiredSignatureError:
            pass
        else:
            return _refresh(node_conf,token_from_file)
    return _login(node_conf)

def _getData(node_conf,endpoint):
    access_token = _getAuthToken(node_conf)
    uri = 'https://'+node_conf['source_node']+'/'+node_conf['tenant']+'/asset_service/api/v1.0/'+endpoint
    for i in range(0,3):
        try:
            response = requests.get(uri,headers={'Authorization':'Bearer '+access_token})
            if response.status_code == 200:
                data = response.json()
                return data
            else:
                logging.error("Connection to Asset Service failed with: "+str(response.status_code))
        except requests.exceptions.RequestException as e:
            logging.error("Connection Error ocurred:"+str(e)+" Retring!") 
            continue
        break
    return None

def _formateData(data,templateName):
    templates = {
            'asset_class':{
                'classname':str,
                'display_name':str,
                'description':str
            },
            'asset':{
                'uuid':uuid.UUID,
                'title':str,
                'summary':str
            },
            'attribute_type':{
                'typename':str,
                'display_name':str,
                'description':str,
                'unique':bool,
                'identifier':bool
            },
            'attribute':{
                'uuid':uuid.UUID,
                'orginal':Attribute,
                'typename':str,
                'asset':Asset,
                'value':str,
                'data':dict,
                'active':bool,
                'is_id':bool
            },
            'class_member':{
                'uuid':uuid.UUID,
                'asset_uuid':str,
                'classname':str
            },
            'relation_type':{
                'typename':str,
                'display_name':str,
                'description':str,
                'unique_src':bool,
                'unique_dst':bool
            },
            'relation':{
                'uuid':uuid.UUID,
                'original':Relation,
                'typename':str,
                'asset_src':Asset,
                'asset_dst':Asset,
                'value':str,
                'data':str,
                'active':bool
            }}
    result = []
    template = templates[templateName]
    templateKeys = template.keys()
    session = sessionmk()
    if data is None:
        return None
    for row in data:
        row_result = {}
        for entry in row:
            if entry in templateKeys:
                if template[entry] == uuid.UUID and row[entry]:
                    row_result[entry] = row[entry]#uuid.UUID(row[entry])
                elif template[entry] in [Asset,Relation,Attribute] and row[entry]:
                    row_result[entry] = session.query(template[entry]).filter(template[entry].uuid == row[entry]).first()
                else:
                    row_result[entry] = row[entry]
        result.append(row_result)
    session.close()
    return result

def _writeTable(entryList,tableModel,tableKey,keyIdentifier):
    session = sessionmk()
    for entry in entryList:
        logging.debug(str(entry))
        tableEntry = tableModel(**entry) ## ** expands dict for 
        existing_query = session.query(tableModel).filter(
            tableKey == entry.get(keyIdentifier))
        existing_entry = existing_query.first()
        if existing_entry == None:
            logging.info("Adding Entry to "+tableModel.__tablename__+": "+entry.get(keyIdentifier))
            session.add(tableEntry)
        else:
            logging.info("Updating Entry in "+tableModel.__tablename__+": "+entry.get(keyIdentifier))
            session.merge(tableEntry)
    session.commit()
    session.close()

def _syncNode(node_conf):
    classes = _formateData(_getData(node_conf,'classes/'),'asset_class')
    if classes:
        _writeTable(classes,AssetClass,AssetClass.classname,'classname')
    assets = _formateData(_getData(node_conf,'assets/'),'asset')
    if assets:
        _writeTable(assets,Asset,Asset.uuid,'uuid')
    members = _formateData(_getData(node_conf,'classes/members/'),'class_member')
    if members:
        _writeTable(members,AssetClassMembership,AssetClassMembership.uuid,'uuid')
    relation_types = _formateData(_getData(node_conf,'relations/types'),'relation_type')
    relations = _formateData(_getData(node_conf,'relations/'),'relation')
    if relation_types and relations:
       _writeTable(relation_types,RelationType,RelationType.typename,'typename')
       _writeTable(relations,Relation,Relation.uuid,'uuid')
    attribute_types = _formateData(_getData(node_conf,'attributes/types'),'attribute_type')
    attributes = _formateData(_getData(node_conf,'attributes/'),'attribute')
    if attribute_types and attributes:
        _writeTable(attribute_types,AttributeType,AttributeType.typename,'typename')
        _writeTable(attributes,Attribute,Attribute.uuid,'uuid')

logging.config.dictConfig(app_conf['logging'])
db = sqlalchemy.create_engine(app_conf['SQLALCHEMY_DATABASE_URI'])
sessionmk = sessionmaker(bind=db)

if __name__ == "__main__":
    nodes = app_conf['asset_sync']
    nodes_sync = map(_syncNode,nodes)

    for node in nodes_sync:
        pass
    pass
