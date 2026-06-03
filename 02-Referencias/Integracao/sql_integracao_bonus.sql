SELECT 
    COMVEN, 
    DATA || ' ' || HORA AS DATA_HORA, 
    USUARIO, 
    VALOR, NUMBOL, 
    PARBOL, LOTEBONUS, 
    SR_RECNO, QUANTIDADE, 
    BONUS, PRECO, 
    TOTAL_ICMS, 
    CODPRO, SUBCOD, 
    OBS, 
    (
        select filial.nome 
        from SAGI_NOME_FILIAL as filial 
        where filial.filial=coalesce((select empresa from cag_rec b where b.numbol=s.numbol limit 1),'') limit 1) as filial 
    FROM sagi_BONUS s 
    where 
        DATA BETWEEN '{data_inicio}' AND '{data_fim}'