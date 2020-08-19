# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions
import base64
from xlrd import open_workbook
import io
import xlsxwriter

class UploadWizard(models.TransientModel):
	_name = "asp.upload_wizard"

	upload = fields.Binary(string="Import File")
	download = fields.Binary(string="Download Disini")
	download_name = fields.Char(string="Nama File")

	@api.multi
	def convert_data(self):
		read = io.BytesIO()
		read.write(base64.decodestring(self.upload)) #decode binary from field, then write (set) it into read variable
		book = open_workbook(file_contents=read.getvalue())
		sheet = book.sheets()[0]

		#SET COLUMN NUMBER FOR EACH VALUE
		account_col = -1
		name_col = -1
		value_col = -1

		for i in range(sheet.ncols):
			if sheet.cell_value(0, i) == "NOMINAL (13,2)":
				value_col = i
			elif sheet.cell_value(0, i) == "NAMA 40":
				name_col = i
			elif sheet.cell_value(0, i) == "NOMER KONTRAK 18":
				account_col = i

		#READ FILE
		temp_array = []
		self.test = sheet.cell_value(1, account_col)
		for i in range(sheet.nrows):
			if i == 0:
				continue
			if i >= 1:
				account = sheet.cell_value(i, account_col)
				account = repr(account).split(".")[0]
				value = sheet.cell_value(i, value_col)
				if account:
					master = self.env['asm.students'].search([('nias', '=', account)])
					if master:
						name = master.full_name
						status = "OK"
						temp_array.append({
							"name": name,
							"account": account,
							"status": status,
							"value": value
						})
					else:
						name = sheet.cell_value(i, name_col)
						if name != "":
							status = "NOT OK"
							temp_array.append({
								"name": name,
								"account": account,
								"status": status,
								"value": value
							})
				else:
					break

		#MAKE NEW FILE
		file_name = '/tmp/upload/up.xlsx'
		workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
		worksheet = workbook.add_worksheet()
		tutorial = workbook.add_worksheet()
		row = 1
		col = 1
		worksheet.write(0, 0, "Status")
		worksheet.write(0, 1, "Student")
		worksheet.write(0, 2, "Nominal Pembayaran")
		worksheet.write(0, 3, "Cara Pembayaran")
		worksheet.write(0, 4, "Jenis Pembayaran")
		worksheet.write(0, 5, "Nomor Kontrak")
		worksheet.write(0, 6, "Confirmation")
		for x in temp_array:
			worksheet.write(row, 0, x['status'])
			worksheet.write(row, 1, x['name'])
			worksheet.write(row, 2, x['value'])
			worksheet.write(row, 3, "auto")
			worksheet.write(row, 4, "spp")
			worksheet.write(row, 5, x['account'])
			worksheet.write(row, 6, "t")
			row += 1
		tutorial.write(0, 0, "Yang dilakukan ketika STATUS berisi PAYMENT ACCOUNT NOT FOUND")
		tutorial.write(1, 0, "1. Cari nama di MASTER STUDENT yang sesuai dengan kolom STUDENT")
		tutorial.write(2, 0, "2. Jika nama yang SESUAI ditemukan, ganti nama di kolom STUDENT dengan nama yang ada dalam MASTER STUDENT")
		tutorial.write(3, 0, "3. Lalu ganti STATUS menjadi OK untuk menandai bahwa STUDENT sudah sesuai")

		workbook.close()
		with open(file_name, "rb") as file:
			file_base64 = base64.b64encode(file.read())
		self.download_name = 'Export File.xlsx'
		self.write({'download': file_base64, })