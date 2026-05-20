#!/usr/bin/env python3
"""Gera PDF do roteiro de apresentação de 15 minutos em docs/."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Roteiro-Apresentacao-15min.pdf"


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle",
            parent=base["Title"],
            fontSize=18,
            spaceAfter=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#1a365d"),
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontSize=14,
            spaceBefore=16,
            spaceAfter=8,
            textColor=colors.HexColor("#2c5282"),
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontSize=12,
            spaceBefore=12,
            spaceAfter=6,
            textColor=colors.HexColor("#2d3748"),
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        ),
        "quote": ParagraphStyle(
            "Quote",
            parent=base["Normal"],
            fontSize=10,
            leading=14,
            leftIndent=18,
            rightIndent=12,
            spaceAfter=8,
            textColor=colors.HexColor("#2d3748"),
            fontName="Helvetica-Oblique",
        ),
        "bullet": ParagraphStyle(
            "Bullet",
            parent=base["Normal"],
            fontSize=10,
            leading=13,
            leftIndent=20,
            bulletIndent=8,
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "Small",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#4a5568"),
        ),
    }


def _table(data: list[list[str]], col_widths: list[float] | None = None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c5282")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def build_story():
    s = _styles()
    story: list = []

    story.append(Paragraph("Roteiro de Apresentação — 15 minutos", s["title"]))
    story.append(
        Paragraph(
            "<b>Pipeline YOLOv8 Pose + AWS</b><br/>"
            "Solução 1: detecção de situações de violência contra a mulher em vídeo",
            s["body"],
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "<i>Sugestão de ritmo: ~120–130 palavras/minuto. "
            "Os blocos somam ~15 min; ajuste 30 s se houver perguntas curtas.</i>",
            s["small"],
        )
    )

    story.append(Paragraph("Visão geral do tempo", s["h1"]))
    story.append(
        _table(
            [
                ["Bloco", "Tópico", "Tempo"],
                ["1", "Documento de arquitetura", "2 min"],
                ["2", "Estrutura do projeto (IaC, Docker/ECS, Python, testes, observabilidade)", "4 min"],
                ["3", "Segurança", "2 min"],
                ["4", "Esteiras CI/CD (GitHub + GitLab)", "2 min"],
                ["5", "Solução 1 — detecção em vídeo + demonstração", "5 min"],
            ],
            col_widths=[1.2 * cm, 11.5 * cm, 2.5 * cm],
        )
    )
    story.append(Spacer(1, 0.4 * cm))

    # --- Bloco 1 ---
    story.append(Paragraph("Bloco 1 — Documento de arquitetura (0:00 – 2:00)", s["h1"]))
    story.append(
        Paragraph(
            "<b>Na tela:</b> docs/Documento de Arquitetura V2.pdf ou "
            "docs/Diagrama de Arquitetura de Infraestrutura V2 BRUNO.png",
            s["body"],
        )
    )
    story.append(Paragraph("O que dizer", s["h2"]))
    story.append(
        Paragraph(
            "«Boa tarde. Vou apresentar a <b>Solução 1</b> deste projeto: análise de vídeo para apoiar "
            "a identificação de situações de violência contra a mulher, usando <b>estimativa de pose</b> "
            "com YOLOv8 e infraestrutura na AWS provisionada como código.»",
            s["quote"],
        )
    )
    story.append(
        Paragraph(
            "«O <b>Documento de Arquitetura V2</b> descreve o sistema de ponta a ponta: desenvolvedor "
            "e repositório GitHub, automação com <b>GitHub Actions</b>, recursos AWS criados por "
            "<b>Terraform</b>, armazenamento em <b>S3</b>, execução em <b>ECS Fargate</b> com imagem "
            "no <b>ECR</b>, e observabilidade em <b>CloudWatch Logs</b>. A versão 2 também documenta "
            "um segundo fluxo — <b>Amazon Transcribe + ChatGPT</b> — para análise de áudio; hoje o "
            "foco é o fluxo de <b>vídeo + pose</b>.»",
            s["quote"],
        )
    )
    story.append(Paragraph("Lista de tecnologias", s["h2"]))
    story.append(
        _table(
            [
                ["Camada", "Tecnologias"],
                ["Aplicação", "Python 3.11, Ultralytics YOLOv8 (pose), OpenCV, NumPy, boto3"],
                ["Container", "Docker (python:3.11-slim), FFmpeg e libs para OpenCV"],
                [
                    "AWS",
                    "S3, ECR, ECS Fargate, IAM (OIDC + task roles), CloudWatch Logs, "
                    "VPC/subnets/IGW/SG",
                ],
                ["IaC", "Terraform ≥ 1.5"],
                [
                    "CI/CD",
                    "GitHub Actions (Ruff, Pytest, build Docker, validate Terraform, push ECR, RunTask)",
                ],
                ["Padrões", "12-factor; pacote src/yolo_violence_pipeline"],
            ],
            col_widths=[3 * cm, 12 * cm],
        )
    )
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Texto resumido do documento", s["h2"]))
    story.append(
        Paragraph(
            "«Em uma frase: o documento explica <b>quem</b> interage com o sistema (dev, CI, container), "
            "<b>onde</b> os dados ficam (buckets S3 de entrada, predict e saída), <b>como</b> o "
            "processamento roda (imagem no ECR, task Fargate sem servidor fixo) e <b>como</b> garantimos "
            "rastreio (logs no CloudWatch) e segurança (sem credenciais no código, IAM por função). "
            "É a referência única para reproduzir o ambiente e alinhar time de dados, infra e produto.»",
            s["quote"],
        )
    )

    story.append(PageBreak())

    # --- Bloco 2 ---
    story.append(Paragraph("Bloco 2 — Estrutura do projeto (2:00 – 6:00)", s["h1"]))
    story.append(
        Paragraph(
            "<b>Na tela:</b> README, pasta terraform/, Dockerfile, "
            "src/yolo_violence_pipeline/, tests/, .github/workflows/",
            s["body"],
        )
    )

    story.append(Paragraph("2.1 Infraestrutura AWS via Terraform (~1 min 30 s)", s["h2"]))
    story.append(
        Paragraph(
            "«Toda a infraestrutura está em terraform/. Um terraform apply cria o ambiente de forma "
            "<b>repetível e versionada</b> — Infrastructure as Code.»",
            s["quote"],
        )
    )
    components = [
        "<b>VPC</b> — por padrão usa a VPC default; opcionalmente create_dedicated_vpc cria VPC dedicada.",
        "<b>Subnets</b> — públicas com map_public_ip_on_launch; em duas AZs na VPC dedicada.",
        "<b>Internet Gateway (IGW)</b> — rota 0.0.0.0/0 → IGW (Fargate baixa imagem do ECR).",
        "<b>Tabelas de roteamento</b> — associadas às subnets públicas.",
        "<b>Security Group</b> — egress liberado para S3, ECR e APIs AWS.",
        "<b>Buckets S3</b> — entrada, predict e saída (YOLO); buckets Transcribe; bloqueio público, SSE-S3, versionamento.",
    ]
    for c in components:
        story.append(Paragraph(f"• {c}", s["bullet"]))

    story.append(Paragraph("2.2 Docker → ECR → ECS Fargate (~1 min)", s["h2"]))
    story.append(
        Paragraph(
            "«O Dockerfile parte de Python 3.11, instala FFmpeg e dependências de vídeo, copia src/ "
            "e instala o projeto. No Amazon ECR ficam as imagens versionadas. O ECS define cluster "
            "Fargate, task definition, execution role e task role. O CI faz build + push; o workflow "
            "RUN pipeline no Fargate dispara ecs run-task com S3_INPUT_KEY.»",
            s["quote"],
        )
    )
    story.append(
        Paragraph(
            "<b>Fluxo:</b> git push → build imagem → docker push ECR → RunTask Fargate → "
            "pipeline → grava em S3 → logs no CloudWatch.",
            s["body"],
        )
    )

    story.append(Paragraph("2.3 Sequência de execução Python (~1 min)", s["h2"]))
    story.append(
        _table(
            [
                ["Passo", "O que acontece"],
                ["1", "CLI yolo-violence process carrega PipelineConfig do ambiente"],
                ["2", "boto3 baixa o vídeo de S3_INPUT_BUCKET + S3_INPUT_KEY"],
                ["3", "Ultralytics carrega o modelo (ex.: yolov8m-pose.pt ou yolov8n-pose.pt)"],
                ["4", "Predict com task=pose, save=True → vídeo skeleton no bucket predict"],
                ["5", "Segunda passagem frame a frame com OpenCV + is_violence_detected"],
                ["6", 'Se disparar, overlay "Violence Detected!" no frame'],
                ["7", "MP4 final enviado ao bucket output"],
            ],
            col_widths=[1.5 * cm, 13.5 * cm],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "«A heurística de violência é um placeholder alinhado ao notebook: conta keypoints visíveis "
            "acima de um limiar — demonstra pose → decisão → vídeo anotado → S3, com espaço para "
            "modelo treinado depois.»",
            s["quote"],
        )
    )

    story.append(Paragraph("2.4 Cobertura de testes (~30 s)", s["h2"]))
    story.append(
        Paragraph(
            "«Testes em tests/ são rápidos e sem baixar pesos YOLO no CI: configuração, heurística "
            "de violência com keypoints falsos, imports Transcribe. No ci-cd.yml: Ruff + Pytest em "
            "push/PR na branch master.»",
            s["quote"],
        )
    )
    story.append(
        _table(
            [
                ["Arquivo", "Foco"],
                ["test_config.py", "Variáveis obrigatórias e defaults"],
                ["test_violence.py", "Heurística placeholder"],
                ["test_transcribe_*.py", "Módulos do fluxo Transcribe"],
            ],
            col_widths=[5 * cm, 10 * cm],
        )
    )

    story.append(Paragraph("2.5 Observabilidade — CloudWatch Logs (~20 s)", s["h2"]))
    story.append(
        Paragraph(
            "«Cada task ECS envia stdout/stderr para o log group /ecs/.../yolo-violence com retenção "
            "de 14 dias. Mensagens como 'Violence no frame N' e erros de S3 aparecem ali — primeiro "
            "lugar para debugar RunTask em PENDING ou falha de download.»",
            s["quote"],
        )
    )

    story.append(PageBreak())

    # --- Bloco 3 ---
    story.append(Paragraph("Bloco 3 — Segurança (6:00 – 8:00)", s["h1"]))

    story.append(Paragraph("3.1 Secrets no GitHub (~45 s)", s["h2"]))
    story.append(
        Paragraph("<b>Na tela:</b> Settings → Secrets and variables → Actions (sem revelar valores).", s["body"])
    )
    story.append(
        _table(
            [
                ["Secret", "Uso"],
                ["AWS_ROLE_ARN", "Assume role via OIDC (sem access key estática)"],
                ["ECR_REPOSITORY_NAME", "Push da imagem"],
                ["ECS_CLUSTER_NAME, ECS_TASK_DEFINITION_FAMILY, ECS_CONTAINER_NAME", "RunTask"],
                ["ECS_SUBNET_IDS, ECS_SECURITY_GROUP_ID", "Rede awsvpc"],
                ["OPENAI_API_KEY", "Apenas fluxo Transcribe (nunca no repositório)"],
            ],
            col_widths=[5.5 * cm, 9.5 * cm],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(
        Paragraph(
            "«Nenhuma chave AWS fica no código nem na imagem Docker. No ECS, credenciais vêm da task role. "
            "No GitHub, usamos OIDC: token de curta duração e role IAM restrita ao repositório.»",
            s["quote"],
        )
    )

    story.append(Paragraph("3.2 IAM e Security Groups (~1 min 15 s)", s["h2"]))
    iam_points = [
        "<b>GitHub Actions (OIDC):</b> provedor token.actions.githubusercontent.com; trust com sub = repo:ORG/REPO:*; permissões ECR, ecs:RunTask, S3/Transcribe.",
        "<b>ECS Execution Role:</b> AmazonECSTaskExecutionRolePolicy — pull de imagem e logs.",
        "<b>ECS Task Role:</b> políticas customizadas somente nos buckets e transcribe:*.",
        "<b>Security Group:</b> apenas egress; sem portas de entrada desnecessárias.",
        "<b>Princípio:</b> menor privilégio — CI não é admin; container não vê secrets do GitHub; buckets não são públicos.",
    ]
    for p in iam_points:
        story.append(Paragraph(f"• {p}", s["bullet"]))

    # --- Bloco 4 ---
    story.append(Paragraph("Bloco 4 — Esteiras CI/CD (8:00 – 10:00)", s["h1"]))
    story.append(Paragraph("<b>Reserve ~2 min para mostrar telas.</b>", s["body"]))

    story.append(Paragraph("GitHub Actions", s["h2"]))
    story.append(
        _table(
            [
                ["Workflow", "Gatilho", "Função"],
                ["ci-cd.yml", "Push/PR master + workflow_dispatch", "Ruff, Pytest, docker build, terraform validate; push ECR"],
                ["run-fargate.yml", "Manual", "Push opcional + RunTask + validação rede"],
                ["aws-transcribe-...yml", "Manual", "Transcribe + ChatGPT (complementar)"],
            ],
            col_widths=[4 * cm, 4.5 * cm, 6.5 * cm],
        )
    )
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("<b>O que mostrar:</b>", s["body"]))
    show_gha = [
        "Aba Actions → último run verde do CI e CD.",
        "Jobs: lint-test, docker-build, terraform-check, publish-ecr.",
        "Workflow RUN pipeline no Fargate → input s3_input_key → log do RunTask.",
    ]
    for item in show_gha:
        story.append(Paragraph(f"• {item}", s["bullet"]))

    story.append(Paragraph("GitLab (~1 min)", s["h2"]))
    story.append(
        Paragraph(
            "«No repositório local o versionamento de pipelines está no GitHub; se a disciplina ou "
            "a empresa usa GitLab, o equivalente seria .gitlab-ci.yml com estágios lint, test, "
            "docker build, terraform validate e deploy com OIDC para AWS. Mostrar captura do GitLab "
            "institucional se exigido pela banca.»",
            s["quote"],
        )
    )
    story.append(
        Paragraph(
            "<i>Nota: não há .gitlab-ci.yml neste repositório — use captura do GitLab da turma ou "
            "explique que o desenho CI é o mesmo, mudando o orquestrador.</i>",
            s["small"],
        )
    )

    story.append(PageBreak())

    # --- Bloco 5 ---
    story.append(Paragraph("Bloco 5 — Solução 1: violência em vídeo + demo (10:00 – 15:00)", s["h1"]))

    story.append(Paragraph("Contexto técnico (1 min)", s["h2"]))
    story.append(
        Paragraph(
            "«A Solução 1 processa vídeos no S3: detecta poses humanas com YOLOv8-pose "
            "(YOLOv8m-pose para maior precisão; YOLOv8n-pose em demo/CI mais leve). OpenCV remonta "
            "o vídeo anotado; boto3 faz download/upload; Python 3.11 no Fargate ou local.»",
            s["quote"],
        )
    )
    story.append(
        Paragraph(
            "<b>Stack:</b> entrada S3 → Ultralytics predict (pose) → keypoints → "
            "is_violence_detected → saída S3 + artefato predict.",
            s["body"],
        )
    )

    story.append(Paragraph("Roteiro da demonstração", s["h2"]))
    story.append(
        _table(
            [
                ["Tempo", "Ação", "O que mostrar"],
                ["10:00–11:00", "Vídeo original", "resultado-detecções-com-yolov8/originais/original-video01.mp4"],
                ["11:00–11:45", "Objeto no S3", "Console AWS → bucket *-input-* → meu_video_04.mp4 ou chave do RunTask"],
                ["11:45–12:30", "Processamento", "Slide fluxo 7 passos ou log CloudWatch"],
                ["12:30–13:30", "Vídeo processado", "resultado-detecções-com-yolov8/processado/video01_violence_detected_*.mp4"],
                ["13:30–14:15", "Saída no S3", "Bucket *-output-* → video_violence_detected_*.mp4"],
                ["14:15–15:00", "Fechamento", "Limitações éticas/técnicas + próximos passos"],
            ],
            col_widths=[2.5 * cm, 3.5 * cm, 9 * cm],
        )
    )

    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph("Falas para a demo", s["h2"]))
    demo_quotes = [
        ("Original", "«Material bruto, sem anotação — gravação que chegaria ao bucket de entrada.»"),
        ("S3 entrada", "«O Fargate lê por chave S3 — desacopla upload do processamento.»"),
        ("Processado", "«YOLOv8-pose gera keypoints; a regra sinaliza frames suspeitos — útil para revisão humana.»"),
        ("S3 saída", "«Resultado versionado no bucket de saída, pronto para dashboard ou perícia.»"),
    ]
    for title, text in demo_quotes:
        story.append(Paragraph(f"<b>{title}:</b> {text}", s["quote"]))

    story.append(Paragraph("Fechamento (30–45 s)", s["h2"]))
    story.append(
        Paragraph(
            "«Resumindo: arquitetura documentada, infra como código, container imutável no ECR, "
            "execução serverless no Fargate, CI/CD com testes e OIDC, e Solução 1 com pose + vídeo "
            "anotado no S3. Próximo passo: substituir placeholder por modelo supervisionado e "
            "avaliar YOLOv8m-pose vs latência no Fargate CPU. Obrigado. Perguntas?»",
            s["quote"],
        )
    )

    story.append(Spacer(1, 0.4 * cm))
    story.append(Paragraph("Checklist pré-apresentação", s["h1"]))
    checklist = [
        "PDF/PNG de arquitetura V2 aberto",
        "Console AWS: buckets input / predict / output",
        "Vídeos local: originais/ e processado/",
        "GitHub Actions: pipeline verde + run-fargate",
        "GitLab: URL/captura institucional (se exigido)",
        "CloudWatch: log stream de execução bem-sucedida",
        "Não exibir valores de secrets na tela",
    ]
    for item in checklist:
        story.append(Paragraph(f"☐ {item}", s["bullet"]))

    story.append(Spacer(1, 0.3 * cm))
    story.append(
        Paragraph(
            "<b>Observação sobre o modelo:</b> YOLOv8m-pose é o alvo de precisão; o default no "
            "Terraform/ECS é yolov8n-pose.pt (mais leve em CPU). Ajuste MODEL_NAME=yolov8m-pose.pt "
            "na task definition para alinhar à apresentação.",
            s["small"],
        )
    )

    story.append(Spacer(1, 0.5 * cm))
    story.append(
        Paragraph(
            "<i>Documento gerado automaticamente a partir do roteiro do projeto "
            "yolo_v8_pose_estimation_code_project.</i>",
            ParagraphStyle("Footer", parent=s["small"], alignment=TA_CENTER),
        )
    )

    return story


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Roteiro de Apresentação — 15 minutos",
        author="YOLO Violence Pipeline",
    )
    doc.build(build_story())
    print(f"PDF gerado: {OUTPUT}")


if __name__ == "__main__":
    main()
