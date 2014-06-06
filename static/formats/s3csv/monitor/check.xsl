<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <!-- **********************************************************************
         Monitor Checks - CSV Import Stylesheet

         CSV fields:
         Name....................monitor_check.name
         Service.................monitor_check.service_id$name
         Script..................monitor_check.function_name
         Comments................monitor_check.comments
         Option:XX...............Option,Value (Option = XX in column name, value = cell in row)

    *********************************************************************** -->
    <xsl:output method="xml"/>

    <!--
    <xsl:include href="../../xml/commons.xsl"/>-->

    <xsl:variable name="ServicePrefix" select="'Service:'"/>

    <!-- ****************************************************************** -->
    <!-- Indexes for faster processing -->
    <xsl:key name="service" match="row" use="col[@field='Service']"/>

    <!-- ****************************************************************** -->
    <xsl:template match="/">
        <s3xml>
            <!-- Services -->
            <xsl:for-each select="//row[generate-id(.)=generate-id(key('service',
                                                                       col[@field='Service'])[1])]">
                <xsl:call-template name="Service" />
            </xsl:for-each>

            <!-- Checks -->
            <xsl:apply-templates select="table/row"/>

        </s3xml>
    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template match="row">

        <!-- Check -->
        <resource name="monitor_check">
            <data field="name"><xsl:value-of select="col[@field='Name']"/></data>
            <data field="function_name"><xsl:value-of select="col[@field='Script']"/></data>

            <xsl:if test="col[@field='Comments']!=''">
                <data field="comments"><xsl:value-of select="col[@field='Comments']"/></data>
            </xsl:if>

            <!-- Link to Service -->
            <reference field="service_id" resource="monitor_service">
                <xsl:attribute name="tuid">
                    <xsl:value-of select="concat($ServicePrefix, col[@field='Service'])"/>
                </xsl:attribute>
            </reference>

            <!-- Options -->
            <xsl:for-each select="col[starts-with(@field, 'Option')]">
                <xsl:call-template name="KeyValue"/>
            </xsl:for-each>

        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="Service">
        <xsl:variable name="ServiceName">
            <xsl:value-of select="col[@field='Service']"/>
        </xsl:variable>

        <resource name="monitor_service">
            <xsl:attribute name="tuid">
                <xsl:value-of select="concat($ServicePrefix, $ServiceName)"/>
            </xsl:attribute>
            <data field="name"><xsl:value-of select="$ServiceName"/></data>
        </resource>

    </xsl:template>

    <!-- ****************************************************************** -->
    <xsl:template name="KeyValue">
        <xsl:variable name="Key" select="normalize-space(substring-after(@field, ':'))"/>
        <xsl:variable name="Value" select="text()"/>

        <!-- Skip empty values, even though these could be useful, otherwise we can't add different options to different checks from the same file -->
        <xsl:if test="$Value!=''">
            <resource name="monitor_check_option">
                <data field="tag"><xsl:value-of select="$Key"/></data>
                <data field="value"><xsl:value-of select="$Value"/></data>
            </resource>
        </xsl:if>

    </xsl:template>

    <!-- ****************************************************************** -->

</xsl:stylesheet>
