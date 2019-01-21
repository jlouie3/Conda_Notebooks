CREATE PROCEDURE SP_GetConfidence
	@MIN_SUPPORT DECIMAL(10,6) = .005,
	@MIN_CONFIDENCE DECIMAL(10,6) = .001
AS
BEGIN
	-- SET NOCOUNT ON added to prevent extra result sets from
	-- interfering with SELECT statements.
	SET NOCOUNT ON;

	WITH Supports AS (
		SELECT DISTINCT ItemId, dbo.FN_CalculateItemSupport(ItemId) AS Support
		FROM TransactionsByDept
	),
	TwoSets AS(
		SELECT 
			s1.ItemId AS ItemId1,
			s2.ItemId AS ItemId2,
			s1.Support,
			dbo.fn_CalculateItemSupport(CONCAT(s1.ItemId,',',s2.ItemId)) AS JointSupport
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
	
END
GO
