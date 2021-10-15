# main.py
import ast
import mysql.connector
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


@app.get("/{search_string}")
def get_search_results(search_string):
	search_string_formated = '%'.join(("%"+search_string.strip()+"%").split(" "))

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
				INNER JOIN union_shipping
				ON joined_result.website_domain = union_shipping.website_domain
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
					"product_price": records[product_id][3],
					"currency_symbol": records[product_id][4],
					"in_stock": records[product_id][5],
					"product_url": records[product_id][6],
					"execution_date": records[product_id][7],
					"shipping_info": ast.literal_eval(records[product_id][8])

			} for product_id in range(len(records))}

		else:
			return {"error": "ERROR IN DABASE CONNECTION!"}

	except:
		return {"message": "ERROR"}
