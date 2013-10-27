from wsgiref.util import setup_testing_defaults
from wsgiref.simple_server import make_server
from pymongo import MongoClient
from bson import json_util
import datetime
import hashlib
import json

class UniqueDataStore:

	def __init__( self ):
		client = MongoClient()
		db = client.unique
		self.doc = db.doc
		self.doc.remove()

	def __call__( self, environ, start_response ):
		if environ['REQUEST_METHOD'] == 'POST':
                        return self._post_response( environ, start_response )

                elif environ['REQUEST_METHOD'] == 'GET':
                        return self._get_response( environ, start_response )

        #Handling logic
        def _post_response( self, environ, start_response ):
                size = int( environ.get('CONTENT_LENGTH', 0) )
                content = environ['wsgi.input'].read( size )
                checksum = self._generate_md5_checksum( content )
		
		store_result = self._store_if_doesnt_exist( size, checksum, content )
		json_record = self._db_to_json_string( store_result[1] )
		if store_result[0]:
			return self._build_conflict_response( start_response, json_record )
		else:
			return self._build_stored_response( start_response, json_record )

	def _get_response( self, environ, start_response ):
                stored_object_list = self._retrieve_record_list()
		json = self._db_to_json_string( stored_object_list )
                return self._build_json_response( start_response, '200 OK', json )

        #Database logic

	#Original version used two methods, new version using one for transactioning
        def _retrieve_conflicting_record( self, size, checksum, content ):
		return self.doc.find_one( { "size" : size, "checksum" : checksum, "content" : content } )

        def _store_content( self, size, checksum, content ):
                record = {
			"size" : size,
			"checksum" : checksum,
			"content" : content,
			}
		id = self.doc.save( record )
		record['_id'] = { "$oid" : id }
		return record

	def _store_if_doesnt_exist( self, size, checksum, content ):
		existed = self.doc.find( { "size" : size, "checksum" : checksum, "content" : content } ).count() != 0
		new_record = self.doc.find_and_modify(
			query={ 'size' : size, 'checksum' : checksum, 'content' : content },
			update={ '$setOnInsert' : { 'size' : size, 'checksum' : checksum, 'content' : content } },
			new=True,
			upsert=True
		)
		return (existed, new_record)
		
        def _retrieve_record_list( self ):
		db_return = self.doc.find()
		to_json = []
		for record in db_return:
			to_json.append( record )
		return to_json

	def _db_to_json_string( self, to_json ):
		return json.dumps( to_json, sort_keys=True, indent=4, default=json_util.default )

        #Response creation
        def _build_json_response( self, start_response, http_code, content ):
                start_response( http_code, [('Content-Type', 'application/json')])
                return [content]

        def _build_stored_response( self, start_response, new_record ):
                return self._build_json_response( start_response, '200 OK', new_record )

        def _build_conflict_response( self, start_response, conflicting_record ):
                return self._build_json_response( start_response, '409 Conflict', conflicting_record )

        #Utility
        def _generate_md5_checksum( self, content ):
                hash_slinging_slasher = hashlib.md5()
                hash_slinging_slasher.update( content )
                hash = hash_slinging_slasher.hexdigest()
                return ( 'md5', hash )

wrapped_app = UniqueDataStore()
httpd = make_server('', 8000, wrapped_app)
print "Serving on port 8000..."
httpd.serve_forever()
