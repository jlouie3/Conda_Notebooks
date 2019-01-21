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
-- Create date: 1/4/2019
-- Description:	Return all items frequently bought with specified item
-- =============================================
CREATE PROCEDURE sp_GetItemsFromTwoSets
	@ItemId INT
AS
BEGIN
	SET NOCOUNT ON;

	SELECT 
		mbts.ItemId2 AS SuggestedItem,
		mbts.Item2Name AS SuggestedItemName
	FROM MarketBasketTwoSets mbts
	WHERE mbts.ItemId1 = @ItemId


END
GO
