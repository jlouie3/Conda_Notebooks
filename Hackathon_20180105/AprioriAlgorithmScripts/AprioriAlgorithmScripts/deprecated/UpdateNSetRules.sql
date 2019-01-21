-- ================================================
-- Template generated from Template Explorer using:
-- Create Procedure (New Menu).SQL
--
-- Use the Specify Values for Template Parameters 
-- command (Ctrl-Shift-M) to fill in the parameter 
-- values below.
--
-- This block of comments will not be included in
-- the definition of the procedure.
-- ================================================
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Jon Louie
-- Create date: 1/3/2019
-- Description:	Generate N-set rules for items above the support and confidence thresholds
-- =============================================
CREATE PROCEDURE sp_UpdateNSetRules
	@MAX_N INT = 3,						-- Largest combination of items to analyze
	@MIN_SUPPORT DECIMAL(19,9) = .005,	-- Used to filter out unpopular items or outliers and save on computation
	@MIN_CONFIDENCE DECIMAL(19,9) = .02	-- Used to filter out any rules that are not compelling enough
AS
BEGIN
	SET NOCOUNT ON;
	
	DROP TABLE IF EXISTS Supports;
	DROP TABLE IF EXISTS JointSupports_2Sets;
	DROP TABLE IF EXISTS JointSupports_3Sets;
	DROP TABLE IF EXISTS JointSupports_4Sets;
	DROP TABLE IF EXISTS Rules_2Sets;
	DROP TABLE IF EXISTS Rules_3Sets;
	DROP TABLE IF EXISTS Rules_4Sets;

	
DECLARE @MIN_SUPPORT DECIMAL(19,9) = .007;		-- Used to filter out unpopular items or outliers and save on computation
DECLARE @MIN_CONFIDENCE DECIMAL(19,9) = .01;	-- Used to filter out any rules that are not compelling enough

DECLARE @TotalTransactions DECIMAL(19,9) = (SELECT COUNT(DISTINCT TransactionId) FROM ProductTransaction);

--------------------------------------------------------------------------	
	WITH Supports AS (
		SELECT 
			ItemId 
			,COUNT(*) / @TotalTransactions AS Support
		FROM ProductTransaction
		GROUP BY ItemId
	)
	SELECT 
		ItemId
		,Support 
	INTO Supports
	FROM Supports
	WHERE Support >= @MIN_SUPPORT
	ORDER BY ItemId
	
	ALTER TABLE Supports
		ALTER COLUMN ItemId INT NOT NULL;
	ALTER TABLE Supports
		ADD CONSTRAINT PK_Supports PRIMARY KEY CLUSTERED (ItemId);

--2------------------------------------------------------------------------	
	;WITH TwoSets AS (
		SELECT 
			s1.ItemId AS ItemId1
			,s2.ItemId AS ItemId2
		FROM (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s1
		CROSS JOIN (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s2
		WHERE s1.ItemId <> s2.ItemId
	)
	,JointSupports_2Sets AS (
		SELECT 
			ts.ItemId1
			,ts.ItemId2 
			,COUNT(*) / @TotalTransactions AS Support
		FROM TwoSets ts
		INNER JOIN ProductTransaction t1
		ON t1.ItemId = ts.ItemId1
		INNER JOIN ProductTransaction t2
		ON t2.ItemId = ts.ItemId2
		AND t2.TransactionId = t1.TransactionId
		GROUP BY ts.ItemId1, ts.ItemId2
	)
	SELECT
		ItemId1,
		ItemId2,
		Support
	INTO JointSupports_2Sets
	FROM JointSupports_2Sets WHERE Support >= @MIN_SUPPORT

	ALTER TABLE JointSupports_2Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE JointSupports_2Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE JointSupports_2Sets
		ADD CONSTRAINT PK_JointSupports_2Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2);
--------------------------------------------------------------------------	
	;WITH Confidence AS(
		SELECT 
			js.ItemId1
			,js.ItemId2
			,js.Support AS JointSupport
			,js.Support / s.Support AS Confidence
			,s.Support AS Item1Support
		FROM JointSupports_2Sets js
		INNER JOIN Supports s
		ON s.ItemId = js.ItemId1
	)
	SELECT 
		c.ItemId1
		,c.ItemId2
		,p1.ItemName AS Item1Name
		,p2.ItemName AS Item2Name
		,c.Confidence
		,c.JointSupport
		,c.Item1Support
		,c.Confidence / c.Item1Support AS Lift
	INTO Rules_2Sets
	FROM Confidence c
	INNER JOIN Product p1
	ON p1.ItemId = c.ItemId1
	INNER JOIN Product p2
	ON p2.ItemId = c.ItemId2
	WHERE c.Confidence >= @MIN_CONFIDENCE
	ORDER BY c.ItemId1, c.ItemId2;
	
	ALTER TABLE Rules_2Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE Rules_2Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE Rules_2Sets
		ADD CONSTRAINT PK_Rules_2Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2);
		
--3------------------------------------------------------------------------	
	;WITH ThreeSets AS (
		SELECT 
			js1.ItemId1
			,js1.ItemId2
			,js2.ItemId1 AS ItemId3
		FROM JointSupports_2Sets js1
		CROSS JOIN JointSupports_2Sets js2
		WHERE js2.ItemId1 <> js1.ItemId1 
		AND   js2.ItemId1 <> js1.ItemId2
	)
	,JointSupports_3Sets AS (
		SELECT 
			ts.ItemId1
			,ts.ItemId2 
			,ts.ItemId3
			,COUNT(*) / @TotalTransactions AS Support
		FROM ThreeSets ts
		INNER JOIN ProductTransaction t1
		ON t1.ItemId = ts.ItemId1
		INNER JOIN ProductTransaction t2
		ON t2.ItemId = ts.ItemId2
		AND t2.TransactionId = t1.TransactionId
		INNER JOIN ProductTransaction t3
		ON t3.ItemId = ts.ItemId3
		AND t3.TransactionId = t2.TransactionId
		GROUP BY ts.ItemId1, ts.ItemId2, ts.ItemId3
	)
	SELECT
		ItemId1,
		ItemId2,
		ItemId3,
		Support
	INTO JointSupports_3Sets
	FROM JointSupports_3Sets WHERE Support >= @MIN_SUPPORT
	
	ALTER TABLE JointSupports_3Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE JointSupports_3Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE JointSupports_3Sets
		ALTER COLUMN ItemId3 INT NOT NULL;
	ALTER TABLE JointSupports_3Sets
		ADD CONSTRAINT PK_JointSupports_3Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2,ItemId3);

--------------------------------------------------------------------------	
DECLARE @MIN_SUPPORT DECIMAL(19,9) = .007;		-- Used to filter out unpopular items or outliers and save on computation
DECLARE @MIN_CONFIDENCE DECIMAL(19,9) = .01;	-- Used to filter out any rules that are not compelling enough

DECLARE @TotalTransactions DECIMAL(19,9) = (SELECT COUNT(DISTINCT TransactionId) FROM ProductTransaction);
drop table if exists Rules_3Sets
	;WITH PermutedSupports AS (
		SELECT 
			js.ItemId1 AS ItemId1
			,js.ItemId2 AS ItemId2
			,js.ItemId3 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
		UNION
		SELECT 
			js.ItemId1 AS ItemId1
			,js.ItemId3 AS ItemId2
			,js.ItemId2 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
		UNION
		SELECT 
			js.ItemId2 AS ItemId1
			,js.ItemId1 AS ItemId2
			,js.ItemId3 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
		UNION
		SELECT 
			js.ItemId2 AS ItemId1
			,js.ItemId3 AS ItemId2
			,js.ItemId1 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
		UNION
		SELECT 
			js.ItemId3 AS ItemId1
			,js.ItemId1 AS ItemId2
			,js.ItemId2 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
		UNION
		SELECT 
			js.ItemId3 AS ItemId1
			,js.ItemId2 AS ItemId2
			,js.ItemId1 AS ItemId3
			,Support
		FROM JointSupports_3Sets js
	)
	--,Confidence AS(
		SELECT DISTINCT
			js3.ItemId1
			,js3.ItemId2
			,js3.ItemId3
			,js3.Support AS JointSupport_3
			,js3.Support / js2.Support AS Confidence
			,js2.Support AS JointSupport_2
		FROM PermutedSupports js3
		INNER JOIN JointSupports_2Sets js2
		ON js2.ItemId1 = js3.ItemId1
		AND js2.ItemId2 = js3.ItemId2
		WHERE js3.Support >= @MIN_SUPPORT
	)
	SELECT 
		c.ItemId1
		,c.ItemId2
		,c.ItemId3
		,p1.ItemName AS Item1Name
		,p2.ItemName AS Item2Name
		,p3.ItemName AS Item3Name
		,c.Confidence
		,c.JointSupport_3
		,c.JointSupport_2
		,c.Confidence / c.JointSupport_2 AS Lift
	INTO Rules_3Sets
	FROM Confidence c
	INNER JOIN Product p1
	ON p1.ItemId = c.ItemId1
	INNER JOIN Product p2
	ON p2.ItemId = c.ItemId2
	INNER JOIN Product p3
	ON p3.ItemId = c.ItemId3
	WHERE c.Confidence >= @MIN_CONFIDENCE
	ORDER BY c.ItemId1, c.ItemId2, c.ItemId3;
	
	ALTER TABLE Rules_3Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE Rules_3Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE Rules_3Sets
		ALTER COLUMN ItemId3 INT NOT NULL;
	ALTER TABLE Rules_3Sets
		ADD CONSTRAINT PK_Rules_3Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2,ItemId3);
--4------------------------------------------------------------------------	
	;WITH FourSets AS (
		SELECT 
			js1.ItemId1
			,js1.ItemId2
			,js1.ItemId3
			,js2.ItemId1 AS ItemId4
		FROM JointSupports_3Sets js1
		CROSS JOIN JointSupports_3Sets js2
		WHERE js2.ItemId1 <> js1.ItemId1 
		AND   js2.ItemId1 <> js1.ItemId2
		AND   js2.ItemId1 <> js1.ItemId3
	)
	,JointSupports_4Sets AS (
		SELECT 
			ts.ItemId1
			,ts.ItemId2 
			,ts.ItemId3
			,ts.ItemId4
			,COUNT(*) / @TotalTransactions AS Support
		FROM FourSets ts
		INNER JOIN ProductTransaction t1
		ON t1.ItemId = ts.ItemId1
		INNER JOIN ProductTransaction t2
		ON t2.ItemId = ts.ItemId2
		AND t2.TransactionId = t1.TransactionId
		INNER JOIN ProductTransaction t3
		ON t3.ItemId = ts.ItemId3
		AND t3.TransactionId = t2.TransactionId
		INNER JOIN ProductTransaction t4
		ON t4.ItemId = ts.ItemId3
		AND t4.TransactionId = t3.TransactionId
		GROUP BY ts.ItemId1, ts.ItemId2, ts.ItemId3, ts.ItemId4
	)
	SELECT
		ItemId1,
		ItemId2,
		ItemId3,
		ItemId4,
		Support
	INTO JointSupports_4Sets
	FROM JointSupports_4Sets WHERE Support >= @MIN_SUPPORT
	
	ALTER TABLE JointSupports_4Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE JointSupports_4Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE JointSupports_4Sets
		ALTER COLUMN ItemId3 INT NOT NULL;
	ALTER TABLE JointSupports_4Sets
		ALTER COLUMN ItemId4 INT NOT NULL;
	ALTER TABLE JointSupports_4Sets
		ADD CONSTRAINT PK_JointSupports_4Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2,ItemId3,ItemId4);

--------------------------------------------------------------------------	
	;WITH Confidence AS(
		SELECT 
			js4.ItemId1
			,js4.ItemId2
			,js4.ItemId3
			,js4.ItemId4
			,js4.Support AS JointSupport_4
			,js4.Support / js3.Support AS Confidence
			,js3.Support AS JointSupport_3
		FROM JointSupports_4Sets js4
		INNER JOIN JointSupports_3Sets js3
		ON js3.ItemId1 = js4.ItemId1
		AND js3.ItemId1 = js4.ItemId2
		WHERE js4.Support >= @MIN_SUPPORT
	)
	SELECT 
		c.ItemId1
		,c.ItemId2
		,c.ItemId3
		,c.ItemId4
		,p1.ItemName AS Item1Name
		,p2.ItemName AS Item2Name
		,p3.ItemName AS Item3Name
		,p4.ItemName AS Item4Name
		,c.Confidence
		,c.JointSupport_4
		,c.JointSupport_3
		,c.Confidence / c.JointSupport_3 AS Lift
	INTO Rules_4Sets
	FROM Confidence c
	INNER JOIN Product p1
	ON p1.ItemId = c.ItemId1
	INNER JOIN Product p2
	ON p2.ItemId = c.ItemId2
	INNER JOIN Product p3
	ON p3.ItemId = c.ItemId3
	INNER JOIN Product p4
	ON p3.ItemId = c.ItemId4
	WHERE c.Confidence >= @MIN_CONFIDENCE
	ORDER BY c.ItemId1, c.ItemId2, c.ItemId3, c.ItemId4;
	
	ALTER TABLE Rules_4Sets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE Rules_4Sets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE Rules_4Sets
		ALTER COLUMN ItemId3 INT NOT NULL;
	ALTER TABLE Rules_4Sets
		ALTER COLUMN ItemId4 INT NOT NULL;
	ALTER TABLE Rules_4Sets
		ADD CONSTRAINT PK_Rules_4Sets PRIMARY KEY CLUSTERED (ItemId1,ItemId2,ItemId3,ItemId4);
END
GO
