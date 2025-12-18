# Integration Testing Checklist

## API Integration
- [ ] Frontend → Backend communication
- [ ] Mobile → Backend communication
- [ ] All endpoints respond correctly
- [ ] Error responses handled properly
- [ ] Timeout handling works

## External Services
- [ ] OpenAI API integration
- [ ] Supabase database connection
- [ ] Playwright browser automation
- [ ] RxNav API (drug interactions)
- [ ] Service failures handled gracefully

## Database Integration
- [ ] Data persistence works
- [ ] Queries return correct data
- [ ] Transactions work correctly
- [ ] Connection pooling works
- [ ] Database migrations apply

## Component Integration
- [ ] Vision → Planner flow
- [ ] Planner → Executor flow
- [ ] Medication → Interaction Checker
- [ ] Diet Advisor → Food Checker
- [ ] Memory/Logging integration

## End-to-End Flows
- [ ] Complete scan → analyze → execute flow
- [ ] Prescription scan → interaction check flow
- [ ] Diet recommendation → meal plan flow
- [ ] Error recovery flows
- [ ] Multi-step workflows

## Data Flow
- [ ] Image upload → processing → storage
- [ ] Intent → plan → execution → results
- [ ] Logging → database → retrieval
- [ ] Screenshot capture → storage → display

