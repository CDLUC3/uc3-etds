<?xml version="1.0" encoding="ISO-8859-1"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
<xsl:output method="text" encoding="utf-8"/>
<!--version 0.2 2014-08-07 -->
<!--2015-10-23: removed "tempdir" parameter from variable newfilename path -->
<!--This stylesheet transforms Proquest ETD metadata into a Merritt ingest API statement -->
<!-- UMI School Codes (DISS_inst_code) for UC campuses:
	ucb:	0028
	ucd:	0029 (note: UCD does not deposit ETDs in Merritt)
	uci:	0030
	ucla:	0031
	ucr:	0032
	ucsd:	0033 
	ucsf:	0034
	ucsb:	0035
	ucsc:	0036
	ucm:	1660
-->
<xsl:strip-space elements="*"/>
<!-- variables to change within stylesheet -->
<xsl:variable name="newfilename" select="concat('/apps/etds/apps/uc3-etds/zipfiles/', substring-after($filename,'zipfiles/'))"/>
<xsl:variable name="surname">
	<xsl:call-template name="replace-string">
		<xsl:with-param name="text" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_surname"/>
		<xsl:with-param name="replace" select='"&apos;"' />
                <xsl:with-param name="with" select='"\x27"'/>
	</xsl:call-template>
</xsl:variable>
<xsl:variable name="fname">
	<xsl:call-template name="replace-string">
		<xsl:with-param name="text" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_fname"/>
		<xsl:with-param name="replace" select='"&apos;"' />
                <xsl:with-param name="with" select='"\x27"'/>
	</xsl:call-template>
</xsl:variable>
<xsl:variable name="mname">
	<xsl:call-template name="replace-string">
		<xsl:with-param name="text" select="/DISS_submission/DISS_authorship/DISS_author/DISS_name/DISS_middle"/>
		<xsl:with-param name="replace" select='"&apos;"' />
                <xsl:with-param name="with" select='"\x27"'/>
	</xsl:call-template>
</xsl:variable>
<xsl:variable name="title">
	<xsl:call-template name="replace-string">
		<xsl:with-param name="text" select="/DISS_submission/DISS_description/DISS_title"/>
		<xsl:with-param name="replace" select='"&apos;"' />
                <xsl:with-param name="with" select='"\x27"'/>
	</xsl:call-template>
</xsl:variable>
<xsl:variable name="date">
	<xsl:call-template name="replace-string">
		<xsl:with-param name="text" select="/DISS_submission/DISS_description/DISS_dates/DISS_comp_date"/>
		<xsl:with-param name="replace" select='"&apos;"' />
                <xsl:with-param name="with" select='"\x27"'/>
	</xsl:call-template>
</xsl:variable>
<!--PQ identifier has form: uc[campus]:[numeric id]. We're changing that to 
have form: PQETD:uc[campus][numeric] -->
<xsl:variable name="vlocalid" select="/DISS_submission/DISS_description/@external_id"/>
<xsl:variable name="localID">
	<xsl:text>PQETD:</xsl:text>
	<xsl:choose>
		<xsl:when test="contains($vlocalid,'http://dissertations.umi.com/')">
			<xsl:value-of select="translate(substring-after($vlocalid,'http://dissertations.umi.com/'),':','')"/>
	    </xsl:when>
		<xsl:when test="contains($vlocalid,'http://oclc.id/')">
  			<xsl:value-of select="translate(substring-after($vlocalid,'http://'),':','')"/>
	    </xsl:when>
		<xsl:otherwise>
			<xsl:value-of select="$vlocalid"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:variable>
<xsl:variable name="inst_code" select="/DISS_submission/DISS_description/DISS_institution/DISS_inst_code"/>
<!-- begin output -->
<xsl:template match="/DISS_submission">
<!--	<xsl:value-of select="$curl"/>
	<xsl:text> </xsl:text>
	<xsl:value-of select="$cert"/>
	<xsl:text> -u </xsl:text>
	<xsl:value-of select="$username"/>
	<xsl:text>:</xsl:text>
	<xsl:value-of select="$password"/>
-->
	<xsl:text>{'file': '</xsl:text>
	<xsl:value-of select="$newfilename"/>
	<xsl:text>', 'type':'container', 'submitter':'ETD_processor','responseForm':'xml','creator':'</xsl:text>
	<xsl:value-of select="$surname"/>
	<xsl:text>, </xsl:text>
	<xsl:value-of select="$fname"/>
	<xsl:text> </xsl:text>
	<xsl:value-of select="$mname"/>
	<xsl:text>', </xsl:text>
	<xsl:text>'localIdentifier':'</xsl:text>
	<xsl:value-of select="$localID"/>
	<xsl:text>','title':'</xsl:text>
	<xsl:value-of select="$title"/>
	<xsl:text>', 'date':'</xsl:text>
	<xsl:value-of select="$date"/>
	<xsl:text>', </xsl:text>	
	<xsl:choose>
		<xsl:when test="$inst_code = '0028'">
			<xsl:text>'profile':'ucb_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0029'">
			<xsl:text>'profile':'NULL' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0030'">
			<xsl:text>'profile':'uci_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0031'">
			<xsl:text>'profile':'ucla_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0032'">
			<xsl:text>'profile':'ucr_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0033'">
			<xsl:text>'profile':'ucsd_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0034'">
			<xsl:text>'profile':'ucsf_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0035'">
			<xsl:text>'profile':'ucsb_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '0036'">
			<xsl:text>'profile':'ucsc_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:when test="$inst_code = '1660'">
			<xsl:text>'profile':'ucm_lib_etd_content' </xsl:text>
		</xsl:when>
		<xsl:otherwise>
			<xsl:text>'profile':'NULL' </xsl:text>
		</xsl:otherwise>
	</xsl:choose>
<!--	<xsl:value-of select="$merrittURL"/> -->
	<xsl:text>}&#xA;</xsl:text>
</xsl:template>
<!--This template inserts a back-slash before a double quotation mark to escape it for the Merritt submission statement -->  
<xsl:template name="replace-string">
	<xsl:param name="text"/>
	<xsl:param name="replace"/>
	<xsl:param name="with"/>
	<xsl:choose>
		<xsl:when test="contains($text,$replace)">
			<xsl:value-of select="substring-before($text,$replace)"/>
			<xsl:value-of select="$with"/>
			<xsl:call-template name="replace-string">
				<xsl:with-param name="text"
                       		select="substring-after($text,$replace)"/>
				<xsl:with-param name="replace" select="$replace"/>
				<xsl:with-param name="with" select="$with"/>
                	</xsl:call-template>
		</xsl:when>
		<xsl:otherwise>
			<xsl:value-of select="$text"/>
		</xsl:otherwise>
	</xsl:choose>
</xsl:template>
</xsl:stylesheet>
