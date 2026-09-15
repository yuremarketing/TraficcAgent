from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'docs/security-audit/relatorio-auditoria-seguranca.pdf'
ASSET = ROOT / 'docs/security-audit'
PALETTE = {'Crítica':'#B91C1C','Alta':'#EA580C','Média':'#D97706','Baixa':'#2563EB','Ponto forte':'#059669'}

findings = [
 ('Alta','docker-compose.yml:11-13','Credenciais PostgreSQL de desenvolvimento estão fixas no Compose (usuário, senha e banco). Se o Compose for exposto ou reutilizado fora de uma rede local isolada, a senha é previsível e reutilizável; não há validação que rejeite esses valores em produção.'),
 ('Média','dist/index.html:12-15','O dashboard grava dados controlados pelo operador em localStorage e os concatena em innerHTML sem escape. Um valor como nome, nicho, produto, site ou status contendo HTML pode executar script no mesmo contexto quando renderizado. A exploração exige escrita no localStorage ou entrada pelo próprio fluxo local.'),
 ('Média','dist/operacao.html:21,23','Eventos de decisão são coletados via prompt, persistidos em localStorage e renderizados em innerHTML sem sanitização. Uma decisão contendo marcação HTML pode executar script ao reabrir/renderizar a operação; a exploração é limitada ao contexto local da aplicação.'),
 ('Alta','traficcagent/__main__.py:1-17; dist/index.html:1-15','Não existe autenticação ou autorização no produto executável: o backend é apenas um smoke test e o painel é HTML estático. Se publicado como sistema multiusuário, qualquer pessoa com acesso à URL poderá operar o painel; os papéis visuais não formam uma barreira no servidor.'),
 ('Média','dist/index.html:12-15; dist/operacao.html:19-23','Não existe isolamento por usuário, organização ou tenant: o estado operacional é global ao perfil do navegador via localStorage. Usuários do mesmo perfil/origem podem ler, alterar, duplicar ou arquivar dados uns dos outros. Isso é uma lacuna de arquitetura do MVP, não um IDOR HTTP.'),
]

from reportlab.platypus import Flowable
class BarChart(Flowable):
    def __init__(self, labels, values, title): self.labels,self.values,self.title=labels,values,title; self.width=16*cm; self.height=4*cm
    def draw(self):
        c=self.canv; c.setFont('Helvetica-Bold',10); c.drawString(0,self.height-12,self.title); maxv=max(self.values+[1]); bw=2.2*cm
        for i,(label,val) in enumerate(zip(self.labels,self.values)):
            x=i*3.1*cm; h=2.2*cm*val/maxv; c.setFillColor(colors.HexColor('#4169E1')); c.rect(x,28,bw,h,fill=1,stroke=0); c.setFillColor(colors.HexColor('#334155')); c.setFont('Helvetica',7); c.drawCentredString(x+bw/2,16,label); c.drawCentredString(x+bw/2,32+h,str(val))
    

def footer(canvas, doc):
    canvas.saveState(); canvas.setFont('Helvetica',8); canvas.setFillColor(colors.HexColor('#64748B')); canvas.drawString(2*cm,1.1*cm,'Relatório de Auditoria de Segurança - TraficcAgent'); canvas.drawRightString(19*cm,1.1*cm,f'Página {doc.page}'); canvas.restoreState()

def issue(n, f):
    sev, loc, desc = f
    return [Paragraph(f'--- ISSUE {n} ---', styles['Heading3']), Paragraph(f'Título: [Segurança] {desc.split(".")[0]}<br/>Labels sugeridas: security + {sev.lower()}<br/><br/><b>Descrição e exploração:</b> {desc}<br/><br/><b>Evidência:</b> {loc}<br/><b>Impacto:</b> risco conforme a condição descrita.<br/><b>Sugestão de correção:</b> remover defaults, implementar auth/tenant server-side e usar textContent, escape ou sanitização allowlist.<br/><b>Critérios de aceite:</b><br/>- [ ] Teste automatizado cobre o caso.<br/>- [ ] Nenhum segredo/default inseguro em produção.<br/>- [ ] Operação autorizada no servidor e vinculada ao tenant.<br/>- [ ] Entrada hostil não executa HTML/JS.<br/>- [ ] Evidência registrada.<br/>--- FIM ISSUE {n} ---', styles['BodyText']), Spacer(1,8)]

styles = getSampleStyleSheet(); styles.add(ParagraphStyle(name='Cover', parent=styles['Title'], alignment=TA_CENTER, fontSize=24, leading=30, textColor=colors.HexColor('#14213D'))); styles.add(ParagraphStyle(name='Small', parent=styles['BodyText'], fontSize=8, leading=10));
def build():
    ASSET.mkdir(parents=True, exist_ok=True); doc=SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=2*cm,leftMargin=2*cm,topMargin=1.8*cm,bottomMargin=1.7*cm); story=[]
    story += [Spacer(1,3*cm), Paragraph('Relatório de Auditoria de Segurança - TraficcAgent',styles['Cover']), Spacer(1,1*cm), Paragraph('Data: 13/09/2026<br/>Escopo: código-fonte, frontend estático, configuração Docker/Cloud Build, histórico Git e bundle frontend.<br/><br/>Nota metodológica: as categorias foram mapeadas para a stack detectada: Python sem framework web/ORM, HTML/CSS/JavaScript estático, localStorage, Docker Compose e Cloud Build. Não foram presumidas rotas, RLS ou auth inexistentes.',styles['BodyText']), PageBreak()]
    story += [Paragraph('Resumo executivo',styles['Heading1']), Paragraph('Foram verificados 5 achados acionáveis: 2 altos e 3 médios. Não foi encontrado achado crítico ou baixo. As categorias IDOR e backend de isolamento por rota não se aplicam porque não há handlers HTTP no repositório.',styles['BodyText']), Spacer(1,8), Table([[Paragraph('<b>Severidade</b>',styles['BodyText']),Paragraph('<b>Total</b>',styles['BodyText'])],[Paragraph('Alta',styles['BodyText']),'2'],[Paragraph('Média',styles['BodyText']),'3'],['Crítica','0'],['Baixa','0']], colWidths=[8*cm,3*cm], style=TableStyle([('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E2E8F0')),('FONTSIZE',(0,0),(-1,-1),9)])), Spacer(1,8)]
    story += [BarChart(['Critica','Alta','Media','Baixa'],[0,2,3,0],'Achados por severidade'), Spacer(1,8), BarChart(['Isolamento','Permissao','IDOR','Chaves','XSS'],[1,1,0,1,2],'Achados por categoria'), PageBreak()]
    story += [Paragraph('Pontos fortes e limitações',styles['Heading1']), Paragraph('<b>Pontos fortes verificados:</b><br/>- Segredos de ambiente estão em .env.example como placeholders vazios; não foram encontradas chaves reais no bundle atual.<br/>- O backend não expõe endpoints HTTP nem queries SQL; portanto não há IDOR HTTP verificável neste snapshot.<br/>- Não há Helm/Terraform nem frontend framework com dangerouslySetInnerHTML; a superfície foi auditada diretamente nos sinks DOM encontrados.<br/><br/><b>Pontos fracos:</b><br/>- O MVP não possui fronteira de identidade, autorização ou tenant.<br/>- Dados do negócio ficam no navegador e HTML é montado por concatenação.<br/>- Compose possui credencial de desenvolvimento fixa.',styles['BodyText']), Spacer(1,10), Paragraph('Achados detalhados',styles['Heading1'])]
    data=[[Paragraph('<b>Severidade</b>',styles['Small']),Paragraph('<b>Arquivo:linha</b>',styles['Small']),Paragraph('<b>Descrição</b>',styles['Small'])]]+[[Paragraph(s,styles['Small']),Paragraph(l,styles['Small']),Paragraph(d,styles['Small'])] for s,l,d in findings]; t=Table(data,colWidths=[2.2*cm,5.2*cm,9.6*cm],repeatRows=1); ts=[('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CBD5E1')),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E2E8F0')),('VALIGN',(0,0),(-1,-1),'TOP')];
    for i,(s,_,_) in enumerate(findings,1): ts.append(('BACKGROUND',(0,i),(0,i),colors.HexColor(PALETTE[s]))); ts.append(('TEXTCOLOR',(0,i),(0,i),colors.white)); t.setStyle(TableStyle(ts)); story += [t, PageBreak(), Paragraph('Recomendações priorizadas',styles['Heading1']), Paragraph('<b>P1</b> Definir autenticação, autorização server-side e modelo de tenant antes de transformar o mockup em produto compartilhado.<br/><b>P2</b> Remover credenciais fixas do Compose e exigir segredos injetados; separar perfil dev/prod e validar startup.<br/><b>P3</b> Eliminar concatenação insegura: preferir textContent/DOM APIs e sanitização allowlist onde HTML for indispensável.<br/><b>P4</b> Criar API persistente com ownership, auditoria, rate limit e testes de autorização; só então executar testes E2E reais.',styles['BodyText']), PageBreak(), Paragraph('ISSUES PARA O GITHUB',styles['Heading1']), Paragraph('Blocos prontos para copiar e colar:',styles['BodyText'])]
    for i,f in enumerate(findings,1): story += issue(i,f)
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
if __name__=='__main__': build()
