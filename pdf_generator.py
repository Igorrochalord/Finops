from fpdf import FPDF
from datetime import datetime

class PDFReport(FPDF):
    def header(self):
        self.set_fill_color(44, 62, 80)
        self.rect(0, 0, 210, 40, 'F')

        self.set_font('Helvetica', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 20, 'Estimativa de Custos de Cloud', align='C', new_x="LMARGIN", new_y="NEXT")

        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, f'Gerado em: {datetime.now().strftime("%d/%m/%Y às %H:%M")}', align='C', new_x="LMARGIN", new_y="NEXT")

        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Cloud Budget Master | Página {self.page_no()}/{{nb}}', align='C')

def create_pdf(cart_items, total_usd, total_brl, dolar_ptax):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, 'Resumo Executivo', new_x="LMARGIN", new_y="NEXT")

    start_y = pdf.get_y()
    pdf.set_fill_color(240, 242, 245)
    pdf.set_draw_color(200, 200, 200)
    pdf.rect(10, start_y, 190, 35, 'FD')

    pdf.set_y(start_y + 5)

    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 8, 'Investimento Mensal (USD):', align='C')

    pdf.cell(95, 8, f'Estimativa Mensal (BRL) - PTAX {dolar_ptax}:', align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('Helvetica', 'B', 18)
    pdf.set_text_color(39, 174, 96)

    pdf.cell(95, 12, f"$ {total_usd:,.2f}", align='C')

    pdf.cell(95, 12, f"R$ {total_brl:,.2f}", align='C', new_x="LMARGIN", new_y="NEXT")

    pdf.ln(25)

    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, 'Detalhamento Técnico da Infraestrutura', new_x="LMARGIN", new_y="NEXT")

    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_fill_color(52, 73, 94)
    pdf.set_text_color(255, 255, 255)

    cols = [30, 35, 75, 20, 30]
    headers = ['Provider', 'Tipo', 'Recurso', 'Qtd', 'Total ($)']
    
    for i, h in enumerate(headers):
        pdf.cell(cols[i], 10, h, border=0, fill=True, align='C')
    pdf.ln()

    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(0, 0, 0)

    fill = False
    for item in cart_items:
        if fill:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)

        resource_name = item['Resource']
        if len(resource_name) > 35:
            resource_name = resource_name[:32] + "..."

        pdf.cell(cols[0], 8, str(item['Provider']), border='B', fill=fill, align='C')
        pdf.cell(cols[1], 8, str(item['Type']), border='B', fill=fill, align='C')
        pdf.cell(cols[2], 8, resource_name, border='B', fill=fill, align='L')
        pdf.cell(cols[3], 8, str(item['Qty']), border='B', fill=fill, align='C')
        pdf.cell(cols[4], 8, f"{item['Total USD']:,.2f}", border='B', fill=fill, align='R')

        pdf.ln()
        fill = not fill

    pdf.ln(10)
    pdf.set_font('Helvetica', 'I', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 5, "Nota: Os valores apresentados são estimativas baseadas em tabelas públicas dos provedores. Impostos (IOF, ICMS) e custos de transferência de dados (Data Transfer Out) podem alterar o valor final.")

    return pdf.output()