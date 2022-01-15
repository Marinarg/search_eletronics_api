# main.py
import ast
import json
import mysql.connector
import pickle
import re

from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Data(BaseModel):
    uniqueId: str
    search: str

@app.get("/{search_string}")
def get_search_results(search_string):

	# Search filters
	if len(search_string) <= 1:
		return None
	if search_string.isdigit():
		return None


	search_string_formated = '%'.join(("%"+search_string.strip()+"%").split(" ")).lower().replace(",", ".")

	try:
		connection = mysql.connector.connect(host='localhost',
	                                         database='eletronics',
	                                         user='root',
	                                         password='pankeka123')

		if connection.is_connected():
			sql_select_query = (
				f"""
				WITH cr AS (
					SELECT product_name, website_domain, product_image, product_price, currency_symbol, in_stock, product_url, execution_date
					FROM crawlers_results cr
					WHERE product_name like '{search_string_formated}'
					AND product_name IS NOT NULL AND product_name != ''
					AND product_price IS NOT NULL AND product_price != ''
					AND in_stock IS NOT NULL AND in_stock != ''
					AND product_url IS NOT NULL AND product_url != ''
				), groupedcr AS (
					SELECT product_name, website_domain, max(execution_date) as max_execution_date
					FROM crawlers_results
					GROUP BY 1,2
				), joined_result AS (
					SELECT DISTINCT cr.product_name, cr.website_domain, cr.product_image, cr.product_price, cr.currency_symbol, cr.in_stock, cr.product_url, execution_date
					FROM cr
					INNER JOIN groupedcr
					ON cr.website_domain = groupedcr.website_domain 
					AND cr.execution_date = groupedcr.max_execution_date
					AND cr.product_name = groupedcr.product_name 
				), filipeflop_shipping AS(
					SELECT response, website_domain 
					FROM shipping_crawlers_results 
					WHERE website_domain='filipeflop' 
					ORDER BY execution_date DESC 
					limit 1
				), baudaeletronica_shipping AS(
					SELECT response, website_domain 
					FROM shipping_crawlers_results 
					WHERE website_domain='baudaeletronica' 
					ORDER BY execution_date DESC 
					limit 1
				), union_shipping AS (
					SELECT *
					FROM filipeflop_shipping
					UNION ALL (SELECT * FROM baudaeletronica_shipping) 
				)
				SELECT *
				FROM joined_result				
				LEFT JOIN union_shipping
				ON joined_result.website_domain = union_shipping.website_domain
				ORDER BY joined_result.in_stock DESC
				"""
			)

			cursor = connection.cursor()
			cursor.execute(sql_select_query)
			records = cursor.fetchall()

			return {
				product_id: {
					"product_name": records[product_id][0],
					"website_domain": records[product_id][1],
					"product_image": records[product_id][2],
					"product_price": re.findall(r"\d+\.*\,*\d*\.*\,*\d*", records[product_id][3])[0],
					"currency_symbol": records[product_id][4],
					"in_stock": records[product_id][5],
					"product_url": records[product_id][6],
					"execution_date": records[product_id][7],
					"shipping_info": ast.literal_eval(records[product_id][8]) if records[product_id][8] else None

			} for product_id in range(len(records))}

		else:
			return {"error": "ERROR IN DABASE CONNECTION!"}

	except:
		return {"message": "ERROR"}

@app.post("/")
def post_search_profile(data: dict):

	connection = mysql.connector.connect(host='localhost',
                                         database='eletronics',
                                         user='root',
                                         password='pankeka123')

	sql_insert_query = (
		f"""
		INSERT INTO search_profiles (unique_id, search) VALUES ('{data["uniqueId"]}', '{data["search"].lower().replace(",", ".")}');
		"""
		)
	cursor = connection.cursor()
	cursor.execute(sql_insert_query)
	connection.commit()

	return {"message": data}

@app.get("/{search_string}/recommendations")
def get_recommendations_results(search_string):

	# Search filters
	if len(search_string) <= 1:
		return None
	if search_string.isdigit():
		return None


	search_string_formated  = search_string.strip().lower().replace(",", ".")

	try:
		connection = mysql.connector.connect(host='localhost',
	                                         database='eletronics',
	                                         user='root',
	                                         password='pankeka123')

		if connection.is_connected():
			# sql_select_query = (
			# 	f"""
			# 	WITH id AS (
			# 		SELECT DISTINCT unique_id, search 
			# 		FROM search_profiles 
			# 		WHERE search = '{search_string_formated}'
			# 	), search AS (
			# 		SELECT s.search 
			# 		FROM search_profiles s 
			# 		INNER JOIN id 
			# 		USING(unique_id)
			# 		WHERE s.search != '{search_string_formated}'
			# 	)

			# 	SELECT search, count('*') as qtt 
			# 	FROM search 
			# 	GROUP BY search 
			# 	ORDER BY qtt DESC 
			# 	LIMIT 5;
			# 	"""
			# )

			# cursor = connection.cursor()
			# cursor.execute(sql_select_query)
			# records = cursor.fetchall()

			# if records and len(records) == 5:
			# 	return [item[0] for item in records]

			# Get stop words from file
			stop_words = json.load(open("/home/admin/stop_words.json"))['stop_words']

			# Get product descriptions and vectorize it (considering stop words)
			sql_get_descriptions_query = (
			    """
			    SELECT DISTINCT product_description 
			    FROM crawlers_results;
			    """
			)

			cursor = connection.cursor()
			cursor.execute(sql_get_descriptions_query)
			records = cursor.fetchall()
			product_descriptions = [item[0] for item in records]

			# # Vectorize search string
			# tfid_vectorizer = TfidfVectorizer(stop_words=stop_words)
			# vectorized_descriptions = tfid_vectorizer.fit_transform(product_descriptions)
			# search_string_vectorized = tfid_vectorizer.transform([search_string_formated])

			# # Load model from disk
			# model = pickle.load(open('/home/admin/kmeans_model.sav', 'rb'))
			
			# # Get recommendation
			# prediction = model.predict(search_string_vectorized)
			# order_centroids = model.cluster_centers_.argsort()[:, ::-1]
			# terms = tfid_vectorizer.get_feature_names()

			# return [terms[ind] for ind in order_centroids[prediction[0], :5]]
			return ['1', '1', '1', '1', '1']

		else:
			return {"error": "ERROR IN DABASE CONNECTION!"}

	except:
		return {"message": "ERROR"}


