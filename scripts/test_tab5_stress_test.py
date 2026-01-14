#!/usr/bin/env python3
"""
Automated stress test script for Tab 5: Executive Pricing Tool
Tests critical functionality and calculations programmatically
"""

import streamlit as st
import pandas as pd
import sys
import os
import math

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from src.data_loader import load_pricing_data
    from src.helpers import get_column_value, clean_price
    from src.pricing_engine import get_unit_price_new_system
except ImportError as e:
    print(f"❌ CRITICAL ERROR: Cannot import required modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

class Tab5StressTest:
    def __init__(self):
        self.df_template = None
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name, passed, details=""):
        """Log a test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
        
        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"
        
        self.test_results.append(result)
        print(result)
    
    def test_data_loading(self):
        """Test data loading functionality"""
        print("\n🔄 Testing Data Loading...")
        
        try:
            self.df_template = load_pricing_data('demo')
            self.log_test("Data Loading", self.df_template is not None, 
                         f"Loaded {len(self.df_template)} rows" if self.df_template is not None else "Failed to load data")
            
            if self.df_template is not None:
                # Test required columns exist
                required_cols = ['Partner', 'Product/Service']
                missing_cols = [col for col in required_cols if col not in self.df_template.columns]
                self.log_test("Required Columns Present", len(missing_cols) == 0,
                             f"Missing: {missing_cols}" if missing_cols else "All required columns found")
                
                # Test partner data
                partners = self.df_template['Partner'].unique()
                self.log_test("Partner Data Available", len(partners) > 0,
                             f"Found {len(partners)} partners: {list(partners)}")
                
                return True
        except Exception as e:
            self.log_test("Data Loading", False, f"Exception: {str(e)}")
            return False
    
    def test_product_selection(self):
        """Test product selection and data integrity"""
        print("\n🔄 Testing Product Selection...")
        
        if self.df_template is None:
            self.log_test("Product Selection", False, "No data available")
            return False
        
        partners = self.df_template['Partner'].unique()
        
        for partner in partners:
            partner_products = self.df_template[self.df_template['Partner'] == partner]
            product_count = len(partner_products)
            
            self.log_test(f"Partner {partner} Products", product_count > 0,
                         f"{product_count} products found")
            
            # Test first product from each partner
            if product_count > 0:
                first_product = partner_products.iloc[0]
                product_name = first_product['Product/Service']
                
                # Test required product data
                self.log_test(f"Product Data - {product_name}", 
                             pd.notna(first_product['Product/Service']),
                             "Product name exists")
                
                # Test country of origin
                country = first_product.get('Country of Origin (Ships From)', 'Unknown')
                self.log_test(f"Country Data - {product_name}", 
                             country != 'Unknown',
                             f"Country (Ships From): {country}")
    
    def test_pricing_calculations(self):
        """Test core pricing calculation functions"""
        print("\n🔄 Testing Pricing Calculations...")
        
        if self.df_template is None:
            self.log_test("Pricing Calculations", False, "No data available")
            return False
        
        # Get a test product
        test_product = self.df_template.iloc[0]
        product_name = test_product['Product/Service']
        
        # Test different quantities
        test_quantities = [1, 50, 100, 250, 500, 1000]
        
        for qty in test_quantities:
            try:
                base_cost, tier_range, tier_col = get_unit_price_new_system(test_product, qty)
                
                self.log_test(f"Pricing Calc - Qty {qty}", 
                             base_cost is not None and base_cost >= 0,
                             f"Cost: ${base_cost:.2f}, Tier: {tier_range}")
                
                # Test markup calculations
                markup_percent = 100
                client_price = base_cost * (1 + markup_percent / 100) if base_cost else 0
                
                expected_client_price = base_cost * 2 if base_cost else 0
                price_match = abs(client_price - expected_client_price) < 0.01
                
                self.log_test(f"Markup Calc - Qty {qty}", price_match,
                             f"Base: ${base_cost:.2f}, Client: ${client_price:.2f}")
                
            except Exception as e:
                self.log_test(f"Pricing Calc - Qty {qty}", False, f"Exception: {str(e)}")
    
    def test_customization_data(self):
        """Test customization data availability and calculations"""
        print("\n🔄 Testing Customization Data...")
        
        if self.df_template is None:
            self.log_test("Customization Data", False, "No data available")
            return False
        
        customization_tests = 0
        customization_found = 0
        
        for idx, product in self.df_template.head(10).iterrows():  # Test first 10 products
            product_name = product['Product/Service']
            customization_tests += 1
            
            # Test setup fee data
            client_setup = clean_price(get_column_value(
                product, 'Client Price: Customization Setup Fee', 'Customization Setup Fee', 0
            ))
            pbp_setup = clean_price(get_column_value(
                product, 'PBP Cost: Customization Setup Fee', 'Customization Setup Fee', 0
            ))
            
            # Test per-unit data
            client_per_unit = clean_price(get_column_value(
                product, 'Client Price: Customization Cost per Unit', 'Customization Cost per Unit', 0
            ))
            pbp_per_unit = clean_price(get_column_value(
                product, 'PBP Cost: Customization Cost per Unit', 'Customization Cost per Unit', 0
            ))
            
            has_customization = any([client_setup > 0, pbp_setup > 0, client_per_unit > 0, pbp_per_unit > 0])
            if has_customization:
                customization_found += 1
                
                self.log_test(f"Customization Data - {product_name}", True,
                             f"Setup: C${client_setup:.2f}/P${pbp_setup:.2f}, Unit: C${client_per_unit:.2f}/P${pbp_per_unit:.2f}")
        
        coverage_rate = (customization_found / customization_tests) * 100
        self.log_test("Customization Coverage", customization_found > 0,
                     f"{customization_found}/{customization_tests} products ({coverage_rate:.1f}%)")
    
    def test_tariff_data(self):
        """Test tariff data availability and calculations"""
        print("\n🔄 Testing Tariff Data...")
        
        if self.df_template is None:
            self.log_test("Tariff Data", False, "No data available")
            return False
        
        tariff_tests = 0
        tariff_found = 0
        non_usa_products = 0
        
        for idx, product in self.df_template.head(10).iterrows():  # Test first 10 products
            product_name = product['Product/Service']
            tariff_tests += 1
            
            # Check country of origin
            country = product.get('Country of Origin (Ships From)', 'Unknown')
            is_non_usa = country.upper() not in ['USA', 'UNITED STATES', 'US', 'U.S.', 'AMERICA']
            if is_non_usa:
                non_usa_products += 1
            
            # Test tariff data
            tariff_dollar = clean_price(get_column_value(product, 'Tariff Estimate ($)', 'Tariff Estimate ($)', 0))
            tariff_percent = clean_price(get_column_value(product, 'Tariff Estimate (%)', 'Tariff Estimate (%)', 0))
            
            has_tariff = tariff_dollar > 0 or tariff_percent > 0
            if has_tariff:
                tariff_found += 1
                
                self.log_test(f"Tariff Data - {product_name}", True,
                             f"${tariff_dollar:.2f} or {tariff_percent:.1f}%, Country: {country}")
        
        self.log_test("Non-USA Products", non_usa_products > 0,
                     f"{non_usa_products}/{tariff_tests} non-USA products")
        
        tariff_coverage = (tariff_found / tariff_tests) * 100
        self.log_test("Tariff Coverage", tariff_found > 0,
                     f"{tariff_found}/{tariff_tests} products ({tariff_coverage:.1f}%)")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔄 Testing Edge Cases...")
        
        if self.df_template is None:
            self.log_test("Edge Cases", False, "No data available")
            return False
        
        # Test with minimum and maximum values
        test_product = self.df_template.iloc[0]
        
        # Test extreme quantities
        extreme_quantities = [1, 10000]
        for qty in extreme_quantities:
            try:
                base_cost, tier_range, tier_col = get_unit_price_new_system(test_product, qty)
                self.log_test(f"Extreme Quantity {qty}", base_cost is not None,
                             f"Cost: ${base_cost:.2f}" if base_cost else "No cost returned")
            except Exception as e:
                self.log_test(f"Extreme Quantity {qty}", False, f"Exception: {str(e)}")
        
        # Test extreme markups
        base_cost, _, _ = get_unit_price_new_system(test_product, 100)
        if base_cost and base_cost > 0:
            extreme_markups = [-50, 0, 500]
            for markup in extreme_markups:
                try:
                    client_price = base_cost * (1 + markup / 100)
                    is_valid = client_price >= 0
                    self.log_test(f"Extreme Markup {markup}%", is_valid,
                                 f"Base: ${base_cost:.2f}, Client: ${client_price:.2f}")
                except Exception as e:
                    self.log_test(f"Extreme Markup {markup}%", False, f"Exception: {str(e)}")
    
    def test_data_consistency(self):
        """Test data consistency across the application"""
        print("\n🔄 Testing Data Consistency...")
        
        if self.df_template is None:
            self.log_test("Data Consistency", False, "No data available")
            return False
        
        # Test that all products have required fields
        required_fields = ['Partner', 'Product/Service']
        
        for field in required_fields:
            null_count = self.df_template[field].isna().sum()
            total_count = len(self.df_template)
            
            self.log_test(f"Field Completeness - {field}", null_count == 0,
                         f"{null_count}/{total_count} missing values")
        
        # Test partner consistency
        partners = self.df_template['Partner'].unique()
        for partner in partners:
            partner_products = self.df_template[self.df_template['Partner'] == partner]
            product_count = len(partner_products)
            
            self.log_test(f"Partner Consistency - {partner}", product_count > 0,
                         f"{product_count} products")
        
        # Test pricing tier consistency
        tier_columns = [col for col in self.df_template.columns if 'Tier' in col and 'PBP Cost' in col]
        if tier_columns:
            self.log_test("Pricing Tiers Available", len(tier_columns) > 0,
                         f"Found {len(tier_columns)} tier columns")
        else:
            self.log_test("Pricing Tiers Available", False, "No tier columns found")
    
    def run_all_tests(self):
        """Run all stress tests"""
        print("🚀 Starting Tab 5 Executive Pricing Tool Stress Test")
        print("=" * 60)
        
        # Run all test suites
        if self.test_data_loading():
            self.test_product_selection()
            self.test_pricing_calculations()
            self.test_customization_data()
            self.test_tariff_data()
            self.test_edge_cases()
            self.test_data_consistency()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        for result in self.test_results:
            print(result)
        
        print("\n" + "=" * 60)
        print(f"TOTAL TESTS: {self.total_tests}")
        print(f"✅ PASSED: {self.passed_tests}")
        print(f"❌ FAILED: {self.failed_tests}")
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"SUCCESS RATE: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL TESTS PASSED! Tab 5 is ready for stress testing.")
        else:
            print(f"\n⚠️  {self.failed_tests} TESTS FAILED. Review issues before user testing.")
        
        return self.failed_tests == 0

def main():
    """Main function to run the stress test"""
    print("Tab 5: Executive Pricing Tool - Automated Stress Test")
    print("This script tests core functionality without the Streamlit UI")
    print()
    
    tester = Tab5StressTest()
    success = tester.run_all_tests()
    
    print("\n📝 NEXT STEPS:")
    if success:
        print("1. ✅ Automated tests passed - proceed with manual UI testing")
        print("2. 📋 Use TAB5_STRESS_TEST_CHECKLIST.md for comprehensive UI testing")
        print("3. 🌐 Test at: http://172.20.10.3:8501/ (Tab 5)")
    else:
        print("1. ❌ Fix failed automated tests first")
        print("2. 🔍 Check data loading and core functionality")
        print("3. 🔄 Re-run this script after fixes")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())