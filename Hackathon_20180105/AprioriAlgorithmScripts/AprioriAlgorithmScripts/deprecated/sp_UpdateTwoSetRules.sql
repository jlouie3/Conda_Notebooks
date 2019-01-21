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
-- Description:	Generate two-set rules for items above the support and confidence thresholds
-- =============================================
CREATE PROCEDURE sp_UpdateTwoSetRules
	@MIN_SUPPORT DECIMAL(19,9) = .005,	-- Used to filter out unpopular items or outliers and save on computation
	@MIN_CONFIDENCE DECIMAL(19,9) = 2.5	-- Used to filter out any rules that are not compelling enough
AS
BEGIN
	SET NOCOUNT ON;
	
	DROP TABLE IF EXISTS MarketBasketTwoSets;

	DECLARE @TotalTransactions DECIMAL(19,9) = (SELECT COUNT(DISTINCT TransactionId) FROM ProductTransaction);
	
	WITH Supports AS (
		SELECT 
			ItemId 
			,COUNT(*) / @TotalTransactions AS Support
		FROM ProductTransaction
		GROUP BY ItemId
	)
	,TwoSets AS (
		SELECT 
			s1.ItemId AS ItemId1
			,s2.ItemId AS ItemId2
		FROM (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s1
		CROSS JOIN (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s2
		WHERE s1.ItemId <> s2.ItemId
	)
	,JointSupports AS (
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
	,Confidence AS(
		SELECT 
			js.ItemId1
			,js.ItemId2
			,js.Support AS JointSupport
			,js.Support / s.Support AS Confidence
			,s.Support AS Item1Support
		FROM JointSupports js
		INNER JOIN Supports s
		ON s.ItemId = js.ItemId1
		WHERE js.Support >= @MIN_SUPPORT
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
	--INTO MarketBasketTwoSets
	FROM Confidence c
	INNER JOIN Product p1
	ON p1.ItemId = c.ItemId1
	INNER JOIN Product p2
	ON p2.ItemId = c.ItemId2
	WHERE c.Confidence >= @MIN_CONFIDENCE
	ORDER BY c.ItemId1, c.ItemId2;
	
	ALTER TABLE MarketBasketTwoSets
		ALTER COLUMN ItemId1 INT NOT NULL;
	ALTER TABLE MarketBasketTwoSets
		ALTER COLUMN ItemId2 INT NOT NULL;
	ALTER TABLE MarketBasketTwoSets
		ADD CONSTRAINT PK_MarketBasketTwoSets PRIMARY KEY CLUSTERED (ItemId1,ItemId2);

END
GO
