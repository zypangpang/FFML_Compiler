CREATE TEMPORARY VIEW `event_1` AS ( SELECT * FROM `transfer` WHERE channel = 'ONL' )
CREATE TEMPORARY VIEW `event_2` AS ( SELECT * FROM event WHERE channel = 'ONL' )
CREATE TEMPORARY VIEW `event_3` AS ( SELECT * FROM event_2 MATCH_RECOGNIZE ( PARTITION BY accountnumber ORDER BY rowtime MEASURES transfer1.id as id,transfer1.rowtime AS rowtime ONE ROW PER MATCH AFTER MATCH SKIP PAST LAST ROW PATTERN (login1 login2 modify_address1 modify_password1 modify_password2 modify_email1 transfer1) WITHIN INTERVAL '5' MINUTE DEFINE login1 AS eventtype='login',login2 AS eventtype='login',modify_address1 AS eventtype='modify_address',modify_password1 AS eventtype='modify_password',modify_password2 AS eventtype='modify_password',modify_email1 AS eventtype='modify_email',transfer1 AS eventtype='transfer' ) )
CREATE TEMPORARY VIEW `event_4` AS ( SELECT * FROM event_1 WHERE id IN ( SELECT id FROM event_3 ) )
CREATE TEMPORARY VIEW `action_1` AS ( SELECT `id`,`accountnumber`,sourcetime,PROCTIME() AS resulttime FROM event_4 )
INSERT INTO alert SELECT * FROM action_1
