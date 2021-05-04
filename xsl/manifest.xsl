<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<!--created by Perry Willett -->
<!--v1.0 2014-03-24 -->
<!--v1.1 2014-06-30: Adding agreement date, local IR embargo period and local IR access option -->
<!--v1.2 2014-07-21: Adding sales_restrict_remove -->
<!--v1.3 2016-01-14: Adding CC License -->
<!--This stylesheets takes a PQ metadata file and outputs a manifest for import into a SQL table -->
<!-- used with etd.sh -->
<xsl:output method="text" encoding="utf-8"/>
<xsl:strip-space elements="*"/>
<xsl:variable name="embargoCode" select="/DISS_submission/@embargo_code"/>
<xsl:variable name="pub_option" select="/DISS_submission/@publishing_option"/>
<xsl:variable name="third_party_search" select="/DISS_submission/@third_party_search"/>
<xsl:variable name="third_party_sales" select="/DISS_submission/@third_party_sales"/>
<xsl:variable name="free_publishing_flag" select="/DISS_submission/@free_publishing_flag"/>
<xsl:variable name="surname" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_surname"/>
<xsl:variable name="fname" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_fname"/>
<xsl:variable name="mname" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_middle"/>
<xsl:variable name="title" select="/DISS_submission/DISS_description/DISS_title"/>
<xsl:variable name="degree" select="/DISS_submission/DISS_description/DISS_degree"/>
<xsl:variable name="dept" select="/DISS_submission/DISS_description/DISS_institution/DISS_inst_contact"/>
<xsl:variable name="adv_fname" select="/DISS_submission/DISS_description/DISS_advisor/DISS_name/DISS_fname"/>
<xsl:variable name="adv_mname" select="/DISS_submission/DISS_description/DISS_advisor/DISS_name/DISS_mname"/>
<xsl:variable name="adv_surname" select="/DISS_submission/DISS_description/DISS_advisor/DISS_name/DISS_surname"/>
<xsl:variable name="agreement_date" select="/DISS_submission/DISS_repository/DISS_agreement_decision_date"/>
<xsl:variable name="local_IR_embargo_period" select="/DISS_submission/DISS_repository/DISS_delayed_release"/>
<xsl:variable name="local_IR_access_option" select="/DISS_submission/DISS_repository/DISS_access_option"/>
<xsl:variable name="vlocalid" select="/DISS_submission/DISS_description/@external_id"/>
<xsl:variable name="localID">
	<xsl:choose>
		<xsl:when test="contains($vlocalid,'http://dissertations.umi.com/')">
			<xsl:value-of select="substring-after($vlocalid,'http://dissertations.umi.com/')"/>
	    </xsl:when>
		<xsl:otherwise>
			<xsl:value-of select="$vlocalid"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:variable>
<xsl:variable name="acceptDate" select="/DISS_submission/DISS_description/DISS_dates/DISS_accept_date"/>
<xsl:variable name="sales_restrict_remove" select="/DISS_submission/DISS_restriction/DISS_sales_restriction/@remove"/>
<xsl:variable name="cc_license" select="/DISS_submission/DISS_creative_commons_license/DISS_abbreviation"/>
<xsl:variable name="aux_file">
        <xsl:choose>
        <xsl:when test="/DISS_submission/DISS_content/DISS_attachment">
                <xsl:text>Y</xsl:text>
        </xsl:when>
        <xsl:otherwise>
                <xsl:text>N</xsl:text>
        </xsl:otherwise>
        </xsl:choose>
</xsl:variable>
<xsl:template match="/DISS_submission">
<xsl:value-of select="$surname"/>
<xsl:text>, </xsl:text>
<xsl:value-of select="$fname"/>
<xsl:text> </xsl:text>
<xsl:value-of select="$mname"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$title"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$acceptDate"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$embargoCode"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$degree"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$dept"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$adv_surname"/>
<xsl:text>, </xsl:text>
<xsl:value-of select="$adv_fname"/>
<xsl:text> </xsl:text>
<xsl:value-of select="$adv_mname"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$localID"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$agreement_date"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$local_IR_embargo_period"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$local_IR_access_option"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$sales_restrict_remove"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$cc_license"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$pub_option"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$third_party_search"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$third_party_sales"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$free_publishing_flag"/>
<xsl:text>&#x9;</xsl:text>
<xsl:value-of select="$aux_file"/>
<xsl:text>&#xA;</xsl:text>
</xsl:template>	
</xsl:stylesheet>
