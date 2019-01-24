SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
-- =============================================
-- Author:		Jon Louie
-- Create date: 12/31/2018
-- Description:	Calculate confidence values for all two-sets using 
--				items with support values over a given threshold
-- =============================================
CREATE FUNCTION fn_Bakery_CalculateTwoSetConfidence
(	
	@MIN_SUPPORT DECIMAL(19,9)
)
RETURNS TABLE 
AS
RETURN 
(
	WITH Supports AS (
		SELECT ItemId, dbo.fn_Bakery_CalculateItemSupport(ItemId) AS Support
		FROM (SELECT DISTINCT ItemId FROM BakeryTransaction) i
	),
	TwoSets AS(
		SELECT 
			s1.ItemId AS ItemId1,
			s2.ItemId AS ItemId2,
			s1.Support,
			dbo.fn_Bakery_CalculateItemSupport(CONCAT(s1.ItemId,',',s2.ItemId)) AS JointSupport
		FROM (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s1
		CROSS JOIN (SELECT * FROM Supports WHERE Support >= @MIN_SUPPORT) s2
		WHERE s1.ItemId <> s2.ItemId
		AND s1.Support >= @MIN_SUPPORT
		AND s2.Support >= @MIN_SUPPORT
	)
	SELECT 
		ItemId1,
		ItemId2, 
		Support/JointSupport AS Confidence 
		,JointSupport
	FROM TwoSets 
	WHERE JointSupport >= @MIN_SUPPORT
)
GO
