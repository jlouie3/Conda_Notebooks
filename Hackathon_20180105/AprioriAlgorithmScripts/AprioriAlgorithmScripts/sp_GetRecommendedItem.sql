
CREATE PROCEDURE mba.sp_GetRecommendedItem(
	-- String of comma-separated ItemIds
	@itemIds VARCHAR(MAX)
) AS
BEGIN
	DROP TABLE IF EXISTS #ItemIds
	
	-- Get ItemIds from input, they must be ordered 
	-- (order matters, smallest itemIds in a Set are always first)
	SELECT 
		ROW_NUMBER() OVER (ORDER BY VALUE) AS Rank
		,VALUE AS ItemId 
	INTO #ItemIds 
	FROM STRING_SPLIT(@itemIds,',') 
	ORDER BY ItemId

	-- Get # of Items in user's basket
	DECLARE @basketSize int = (select count(*) from #ItemIds);

	-- Choose correct recommendation table based on basket size
	IF @basketSize = 1
	BEGIN
		SELECT NextItem_Id, NextItem FROM mba.Set_2_Confidence
		WHERE BasketItem1_Id = (SELECT ItemId FROM #ItemIds WHERE Rank = 1)
	END

	IF @basketSize = 2
	BEGIN
		SELECT NextItem_Id, NextItem FROM mba.Set_3_Confidence
		WHERE BasketItem1_Id = (SELECT ItemId FROM #ItemIds WHERE Rank = 1)
			AND BasketItem2_Id = (SELECT ItemId FROM #ItemIds WHERE Rank = 2)
	END

END